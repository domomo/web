import pytest
from types import SimpleNamespace
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import createToken
from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.models.board import Board
from app.models.purchase import Purchase
from app.models.user import User


@pytest.fixture
def sales_client(monkeypatch):
    monkeypatch.setattr(settings, "SECRET_KEY", "paid-article-test-secret-key-at-least-32-bytes")
    monkeypatch.setattr(settings, "PORTONE_STORE_ID", "store-test")
    monkeypatch.setattr(settings, "PORTONE_CHANNEL_KEY", "channel-test")
    monkeypatch.setattr(settings, "PORTONE_API_SECRET", "portone-secret-test")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(autoflush=False, bind=engine)

    def override_db():
        with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, sessions
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)
    engine.dispose()


def _user(sessions, *, email, name, kakao_user_id=None):
    with sessions() as db:
        user = User(email=email, password="pw" if email else None, name=name, kakao_user_id=kakao_user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.idx


def _cookie_for(sessions, user_idx):
    with sessions() as db:
        user = db.get(User, user_idx)
        subject = user.email or f"kakao:{user.kakao_user_id}"
    return {"EN_AT": createToken(subject)}


def _auth_headers(sessions, user_idx):
    token = _cookie_for(sessions, user_idx)["EN_AT"]
    return {"Cookie": f"EN_AT={token}"}


def _pay_for(client, sessions, user_idx, board_idx, monkeypatch, amount):
    prepared = client.post("/api/purchases/prepare", headers=_auth_headers(sessions, user_idx), json={"board_idx": board_idx})
    assert prepared.status_code == 200
    payment_id = prepared.json()["payment_id"]
    monkeypatch.setattr("app.api.routers.purchase.requests.get", lambda *args, **kwargs: SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"id": payment_id, "status": "PAID", "amount": {"total": amount}, "currency": "KRW"},
    ))
    confirmed = client.post("/api/purchases/confirm", headers=_auth_headers(sessions, user_idx), json={"payment_id": payment_id})
    return prepared, confirmed


def test_free_article_list_and_detail_remain_public(sales_client):
    client, _ = sales_client
    written = client.post("/api/board/write", json={"title": "무료", "contents": "전체 본문", "category": "과학/IT"})
    assert written.status_code == 200
    idx = written.json()["idx"]
    detail = client.get(f"/api/board/read/{idx}")
    listing = client.get("/api/board/list").json()[0]
    for response in (detail.json(), listing):
        assert response["contents"] == "전체 본문"
        assert response["sale_price"] is None
        assert response["is_for_sale"] is False
        assert response["is_author"] is False
        assert response["has_purchased"] is False


def test_article_list_can_filter_free_and_paid_posts(sales_client):
    client, sessions = sales_client
    author_idx = _user(sessions, email="author@example.com", name="작성자")
    client.post("/api/board/write", json={"title": "무료", "contents": "본문", "category": "과학/IT"})
    client.post("/api/board/write", headers=_auth_headers(sessions, author_idx), json={
        "title": "유료", "contents": "본문", "category": "과학/IT", "sale_price": 1000, "preview": "미리보기",
    })
    free = client.get("/api/board/list?sale_type=free").json()
    paid = client.get("/api/board/list?sale_type=paid").json()
    assert [item["title"] for item in free] == ["무료"]
    assert [item["title"] for item in paid] == ["유료"]


def test_paid_article_requires_positive_price_and_nonblank_preview(sales_client):
    client, _ = sales_client
    for price, preview in [(0, "미리보기"), (-1, "미리보기"), (1000, "   ")]:
        response = client.post("/api/board/write", json={
            "title": "유료", "contents": "본문", "category": "과학/IT",
            "sale_price": price, "preview": preview,
        })
        assert response.status_code == 422


def test_paid_article_requires_login_and_sets_author_from_cookie(sales_client):
    client, sessions = sales_client
    anonymous = client.post("/api/board/write", json={
        "title": "유료", "contents": "본문", "category": "과학/IT",
        "sale_price": 1000, "preview": "공개 미리보기",
    })
    assert anonymous.status_code == 401
    author_idx = _user(sessions, email="author@example.com", name="작성자")
    response = client.post("/api/board/write", headers=_auth_headers(sessions, author_idx), json={
        "title": "유료", "contents": "본문", "category": "과학/IT",
        "sale_price": 1000, "preview": "공개 미리보기",
    })
    assert response.status_code == 200
    body = response.json()
    assert body["author_name"] == "작성자" and body["sale_price"] == 1000
    with sessions() as db:
        assert db.get(Board, body["idx"]).author_idx == author_idx


def test_unpurchased_reader_gets_preview_but_not_contents(sales_client):
    client, sessions = sales_client
    author_idx = _user(sessions, email="author@example.com", name="작성자")
    response = client.post("/api/board/write", headers=_auth_headers(sessions, author_idx), json={
        "title": "유료", "contents": "비공개 본문", "category": "과학/IT",
        "sale_price": 1000, "preview": "공개 미리보기",
    })
    idx = response.json()["idx"]
    reader_idx = _user(sessions, email="reader@example.com", name="독자")
    detail = client.get(f"/api/board/read/{idx}", headers=_auth_headers(sessions, reader_idx)).json()
    assert detail["contents"] is None
    assert detail["preview"] == "공개 미리보기" and detail["has_purchased"] is False


def test_author_and_buyer_get_full_contents(sales_client, monkeypatch):
    client, sessions = sales_client
    author_idx = _user(sessions, email="author@example.com", name="작성자")
    idx = client.post("/api/board/write", headers=_auth_headers(sessions, author_idx), json={
        "title": "유료", "contents": "비공개 본문", "category": "과학/IT",
        "sale_price": 1200, "preview": "미리보기",
    }).json()["idx"]
    author = client.get(f"/api/board/read/{idx}", headers=_auth_headers(sessions, author_idx)).json()
    assert author["contents"] == "비공개 본문" and author["is_author"] is True
    buyer_idx = _user(sessions, email="buyer@example.com", name="구매자")
    _, purchase = _pay_for(client, sessions, buyer_idx, idx, monkeypatch, 1200)
    assert purchase.status_code == 200
    buyer = client.get(f"/api/board/read/{idx}", headers=_auth_headers(sessions, buyer_idx)).json()
    assert buyer["contents"] == "비공개 본문" and buyer["has_purchased"] is True


def test_purchase_is_idempotent_and_unlocks_contents(sales_client, monkeypatch):
    client, sessions = sales_client
    author_idx = _user(sessions, email="author@example.com", name="작성자")
    buyer_idx = _user(sessions, email="buyer@example.com", name="구매자")
    idx = client.post("/api/board/write", headers=_auth_headers(sessions, author_idx), json={
        "title": "유료", "contents": "본문", "category": "과학/IT",
        "sale_price": 1200, "preview": "미리보기",
    }).json()["idx"]
    prepared, first = _pay_for(client, sessions, buyer_idx, idx, monkeypatch, 1200)
    second = client.post("/api/purchases/confirm", headers=_auth_headers(sessions, buyer_idx), json={"payment_id": prepared.json()["payment_id"]})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    with sessions() as db:
        assert db.scalar(select(Purchase).where(Purchase.board_idx == idx, Purchase.buyer_idx == buyer_idx)) is not None
        assert db.query(Purchase).count() == 1


def test_unverified_payment_does_not_grant_article_access(sales_client, monkeypatch):
    client, sessions = sales_client
    author_idx = _user(sessions, email="author@example.com", name="작성자")
    buyer_idx = _user(sessions, email="buyer@example.com", name="구매자")
    idx = client.post("/api/board/write", headers=_auth_headers(sessions, author_idx), json={
        "title": "유료", "contents": "비공개 본문", "category": "과학/IT", "sale_price": 1200, "preview": "미리보기",
    }).json()["idx"]
    prepared = client.post("/api/purchases/prepare", headers=_auth_headers(sessions, buyer_idx), json={"board_idx": idx}).json()
    monkeypatch.setattr("app.api.routers.purchase.requests.get", lambda *args, **kwargs: SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"id": prepared["payment_id"], "status": "PAID", "amount": {"total": 1}, "currency": "KRW"},
    ))
    response = client.post("/api/purchases/confirm", headers=_auth_headers(sessions, buyer_idx), json={"payment_id": prepared["payment_id"]})
    assert response.status_code == 409
    monkeypatch.setattr("app.api.routers.purchase.requests.get", lambda *args, **kwargs: SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {"id": "different-payment", "status": "PAID", "amount": {"total": 1200}, "currency": "KRW"},
    ))
    mismatched_id = client.post("/api/purchases/confirm", headers=_auth_headers(sessions, buyer_idx), json={"payment_id": prepared["payment_id"]})
    assert mismatched_id.status_code == 409
    detail = client.get(f"/api/board/read/{idx}", headers=_auth_headers(sessions, buyer_idx)).json()
    assert detail["contents"] is None and detail["has_purchased"] is False


def test_pre_portone_purchase_row_does_not_unlock_article(sales_client):
    client, sessions = sales_client
    author_idx = _user(sessions, email="author@example.com", name="작성자")
    buyer_idx = _user(sessions, email="buyer@example.com", name="구매자")
    idx = client.post("/api/board/write", headers=_auth_headers(sessions, author_idx), json={
        "title": "유료", "contents": "비공개 본문", "category": "과학/IT", "sale_price": 1200, "preview": "미리보기",
    }).json()["idx"]
    with sessions() as db:
        db.add(Purchase(buyer_idx=buyer_idx, board_idx=idx, price=1200))
        db.commit()
    detail = client.get(f"/api/board/read/{idx}", headers=_auth_headers(sessions, buyer_idx)).json()
    assert detail["contents"] is None and detail["has_purchased"] is False


def test_author_cannot_purchase_own_article(sales_client):
    client, sessions = sales_client
    author_idx = _user(sessions, email="author@example.com", name="작성자")
    idx = client.post("/api/board/write", headers=_auth_headers(sessions, author_idx), json={
        "title": "유료", "contents": "본문", "category": "과학/IT", "sale_price": 1000, "preview": "미리보기",
    }).json()["idx"]
    response = client.post("/api/purchases/prepare", headers=_auth_headers(sessions, author_idx), json={"board_idx": idx})
    assert response.status_code == 409


def test_free_or_missing_article_cannot_be_purchased(sales_client):
    client, sessions = sales_client
    buyer_idx = _user(sessions, email="buyer@example.com", name="구매자")
    free_idx = client.post("/api/board/write", json={"title": "무료", "contents": "본문", "category": "과학/IT"}).json()["idx"]
    free = client.post("/api/purchases/prepare", headers=_auth_headers(sessions, buyer_idx), json={"board_idx": free_idx})
    missing = client.post("/api/purchases/prepare", headers=_auth_headers(sessions, buyer_idx), json={"board_idx": 99999})
    assert free.status_code == 409 and missing.status_code == 404


def test_purchase_requires_valid_en_at_cookie(sales_client):
    client, _ = sales_client
    absent = client.post("/api/purchases/prepare", json={"board_idx": 1})
    invalid = client.post("/api/purchases/prepare", headers={"Cookie": "EN_AT=invalid"}, json={"board_idx": 1})
    assert absent.status_code == 401
    assert invalid.status_code == 401
    openapi = client.get("/openapi.json").json()
    assert set(openapi["paths"]["/api/purchases/prepare"]["post"]["responses"]) >= {"200", "401", "404", "409", "503"}
    assert "401" in openapi["paths"]["/api/board/write"]["post"]["responses"]


def test_public_payment_config_never_exposes_api_secret(sales_client):
    client, _ = sales_client
    response = client.get("/api/purchases/config")
    assert response.status_code == 200
    assert response.json() == {"configured": True, "store_id": "store-test", "channel_key": "channel-test"}
    assert "api_secret" not in response.json()

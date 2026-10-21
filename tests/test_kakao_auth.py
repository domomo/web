import os

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.services.kakao import KakaoOAuthClient, KakaoOAuthError
from app.db.database import Base, get_db
from app.main import app
from app.models.user import User
from app.api.routers.user import get_kakao_client
from app.core import security


def test_kakao_oauth_client_exchanges_code_and_reads_only_nickname():
    requests = []

    def provider(request):
        requests.append(request)
        if request.url.path == "/oauth/token":
            assert request.method == "POST"
            assert request.content.decode().find("authorization_code") >= 0
            return httpx.Response(200, json={"access_token": "access"})
        assert request.url.path == "/v2/user/me"
        assert request.headers["Authorization"] == "Bearer access"
        assert request.url.params["property_keys"] == '["kakao_account.profile"]'
        return httpx.Response(200, json={
            "id": 12345,
            "kakao_account": {"profile": {"nickname": "  노트 사용자  "}, "email": "ignored@example.com"},
        })

    with httpx.Client(transport=httpx.MockTransport(provider)) as http:
        kakao = KakaoOAuthClient("rest-key", "client-secret", "http://localhost/callback", http)
        profile = kakao.user_from_code("auth-code")
    assert profile.user_id == "12345"
    assert profile.nickname == "노트 사용자"
    assert len(requests) == 2
    assert b"client_secret=client-secret" in requests[0].content


@pytest.mark.parametrize("handler", [
    lambda request: httpx.Response(500, json={"error": "bad"}),
    lambda request: httpx.Response(200, content="not-json"),
    lambda request: httpx.Response(200, json={"access_token": "token"})
        if request.url.path == "/oauth/token" else httpx.Response(200, json={"id": 1}),
])
def test_kakao_provider_errors_are_normalized(handler):
    with httpx.Client(transport=httpx.MockTransport(handler)) as http:
        kakao = KakaoOAuthClient("rest-key", None, "http://localhost/callback", http)
        with pytest.raises(KakaoOAuthError):
            kakao.user_from_code("code")


def test_kakao_provider_timeout_is_normalized():
    def timeout(_request):
        raise httpx.ReadTimeout("provider timed out")

    with httpx.Client(transport=httpx.MockTransport(timeout)) as http:
        kakao = KakaoOAuthClient("rest-key", None, "http://localhost/callback", http)
        with pytest.raises(KakaoOAuthError):
            kakao.user_from_code("code")


def test_kakao_oauth_client_rejects_missing_credentials():
    kakao = KakaoOAuthClient(None, None, "http://localhost/callback")
    with pytest.raises(KakaoOAuthError):
        kakao.user_from_code("code")
    kakao.close()


def test_token_creation_does_not_print_the_signing_secret(monkeypatch, capsys):
    monkeypatch.setattr(security.settings, "SECRET_KEY", "test-only-secret-that-is-long-enough")
    security.createToken("kakao:test-user")
    assert capsys.readouterr().out == ""


@pytest.fixture
def auth_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(autoflush=False, bind=engine)

    def override_db():
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, testing_session
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(engine)
    engine.dispose()


class StubKakao:
    def __init__(self, profile=None, error=None):
        self.profile = profile
        self.error = error

    def user_from_code(self, code):
        if self.error:
            raise self.error
        return self.profile


def set_provider(provider):
    app.dependency_overrides[get_kakao_client] = lambda: provider


def test_kakao_state_sets_short_lived_http_only_cookie(auth_client):
    client, _ = auth_client
    response = client.get("/api/user/kakao/state")
    assert response.status_code == 200
    assert response.json()["redirect_uri"].endswith("/api/user/kakao/callback")
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie and "max-age=300" in cookie
    assert "path=/api/user/kakao/callback" in cookie
    assert response.json()["state"] == client.cookies["kakao_oauth_state"]


def test_kakao_callback_creates_nickname_only_user_and_sets_en_at(auth_client):
    client, sessions = auth_client
    set_provider(StubKakao(profile=type("Profile", (), {"user_id": "k-1", "nickname": "새 사용자"})()))
    state = client.get("/api/user/kakao/state").json()["state"]
    response = client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False)
    assert response.status_code == 302 and response.headers["location"] == "/posts"
    assert "EN_AT=" in response.headers["set-cookie"]
    with sessions() as session:
        user = session.scalar(select(User).where(User.kakao_user_id == "k-1"))
        assert user.name == "새 사용자" and user.email is None and user.password is None


def test_current_user_returns_kakao_profile_from_session_cookie(auth_client):
    client, _ = auth_client
    set_provider(StubKakao(profile=type("Profile", (), {"user_id": "k-me", "nickname": "프로필 사용자"})()))
    state = client.get("/api/user/kakao/state").json()["state"]
    client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False)

    response = client.get("/api/user/me")

    assert response.status_code == 200
    assert response.json() == {"email": None, "name": "프로필 사용자"}


def test_current_user_requires_a_valid_session(auth_client):
    client, _ = auth_client

    response = client.get("/api/user/me")

    assert response.status_code == 401


def test_password_login_cookie_works_over_local_http(auth_client, monkeypatch):
    client, sessions = auth_client
    with sessions() as session:
        session.add(User(email="local@example.com", password="password", name="Local User"))
        session.commit()
    monkeypatch.setattr("app.api.routers.user.settings.KAKAO_REDIRECT_URI", "http://localhost:8000/api/user/kakao/callback")

    response = client.post("/api/user/login", json={"email": "local@example.com", "password": "password"})

    assert response.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()
    assert "secure" not in response.headers["set-cookie"].lower()
    current_user = client.get("/api/user/me")
    assert current_user.status_code == 200
    assert current_user.json() == {"email": "local@example.com", "name": "Local User"}

    logout = client.post("/api/user/logout")

    assert logout.status_code == 200
    assert logout.json() == {"message": "로그아웃되었습니다."}
    deleted_cookie = logout.headers["set-cookie"].lower()
    assert "en_at=\"\"" in deleted_cookie or "en_at=;" in deleted_cookie
    assert "path=/" in deleted_cookie and "max-age=0" in deleted_cookie
    assert "secure" not in deleted_cookie
    assert client.get("/api/user/me").status_code == 401


def test_kakao_callback_reuses_existing_user_without_email_linking(auth_client):
    client, sessions = auth_client
    with sessions() as session:
        session.add(User(email="same@example.com", password="pw", name="Local"))
        session.commit()
    set_provider(StubKakao(profile=type("Profile", (), {"user_id": "k-2", "nickname": "Kakao"})()))
    state = client.get("/api/user/kakao/state").json()["state"]
    response = client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False)
    assert response.headers["location"] == "/posts"
    with sessions() as session:
        assert session.query(User).count() == 2
        assert session.scalar(select(User).where(User.kakao_user_id == "k-2")).email is None


def test_kakao_callback_reuses_existing_kakao_account(auth_client):
    client, sessions = auth_client
    with sessions() as session:
        session.add(User(email=None, password=None, name="Original", kakao_user_id="k-repeat"))
        session.commit()
    set_provider(StubKakao(profile=type("Profile", (), {"user_id": "k-repeat", "nickname": "Changed"})()))
    state = client.get("/api/user/kakao/state").json()["state"]
    response = client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False)
    assert response.headers["location"] == "/posts"
    with sessions() as session:
        assert session.query(User).count() == 1
        assert session.scalar(select(User).where(User.kakao_user_id == "k-repeat")).name == "Original"


@pytest.mark.parametrize("callback_state", [None, "wrong"])
def test_kakao_callback_rejects_missing_or_mismatched_state(auth_client, callback_state):
    client, _ = auth_client
    client.get("/api/user/kakao/state")
    params = {"code": "code"}
    if callback_state is not None:
        params["state"] = callback_state
    response = client.get("/api/user/kakao/callback", params=params, follow_redirects=False)
    assert response.headers["location"] == "/login?oauth_error=invalid_state"
    assert "kakao_oauth_state=" in response.headers["set-cookie"]
    assert "max-age=0" in response.headers["set-cookie"].lower()


def test_kakao_state_is_single_use(auth_client):
    client, _ = auth_client
    set_provider(StubKakao(profile=type("Profile", (), {"user_id": "k-3", "nickname": "Kakao"})()))
    state = client.get("/api/user/kakao/state").json()["state"]
    assert client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False).headers["location"] == "/posts"
    repeated = client.get("/api/user/kakao/callback", params={"code": "again", "state": state}, follow_redirects=False)
    assert repeated.headers["location"] == "/login?oauth_error=invalid_state"


def test_kakao_callback_handles_provider_cancel_and_failure(auth_client):
    client, _ = auth_client
    state = client.get("/api/user/kakao/state").json()["state"]
    cancelled = client.get("/api/user/kakao/callback", params={"error": "access_denied", "state": state}, follow_redirects=False)
    assert cancelled.headers["location"] == "/login?oauth_error=cancelled"
    set_provider(StubKakao(error=KakaoOAuthError("provider_error")))
    state = client.get("/api/user/kakao/state").json()["state"]
    failure = client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False)
    assert failure.headers["location"] == "/login?oauth_error=provider_error"


def test_kakao_callback_rejects_missing_nickname(auth_client):
    client, _ = auth_client
    set_provider(StubKakao(error=KakaoOAuthError("profile_incomplete")))
    state = client.get("/api/user/kakao/state").json()["state"]
    response = client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False)
    assert response.headers["location"] == "/login?oauth_error=profile_error"


def test_kakao_callback_handles_database_error_safely(auth_client, monkeypatch):
    from sqlalchemy.orm import Session

    client, _ = auth_client
    set_provider(StubKakao(profile=type("Profile", (), {"user_id": "k-db", "nickname": "Kakao"})()))
    state = client.get("/api/user/kakao/state").json()["state"]

    def fail_commit(self):
        raise RuntimeError("database detail")

    monkeypatch.setattr(Session, "commit", fail_commit)
    response = client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False)
    assert response.headers["location"] == "/login?oauth_error=server_error"


def test_concurrent_first_kakao_login_reuses_unique_account(auth_client, monkeypatch):
    from sqlalchemy.orm import Session

    client, sessions = auth_client
    with sessions() as session:
        session.add(User(email=None, password=None, name="First", kakao_user_id="k-race"))
        session.commit()
    original_scalar = Session.scalar
    first_lookup = {"pending": True}

    def simulate_race(self, statement, *args, **kwargs):
        if first_lookup["pending"] and "kakao_user_id" in str(statement):
            first_lookup["pending"] = False
            return None
        return original_scalar(self, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "scalar", simulate_race)
    set_provider(StubKakao(profile=type("Profile", (), {"user_id": "k-race", "nickname": "Kakao"})()))
    state = client.get("/api/user/kakao/state").json()["state"]
    response = client.get("/api/user/kakao/callback", params={"code": "code", "state": state}, follow_redirects=False)
    assert response.headers["location"] == "/posts"
    with sessions() as session:
        assert session.query(User).count() == 1


def test_kakao_oauth_client_against_postman_simulation():
    base_url = os.getenv("KAKAO_SIMULATION_URL")
    if not base_url:
        pytest.skip("set KAKAO_SIMULATION_URL to run the Postman Kakao simulation")
    kakao = KakaoOAuthClient(
        "simulation-rest-key",
        None,
        "http://localhost:8000/api/user/kakao/callback",
        token_url=f"{base_url.rstrip('/')}/kakao/kauth/oauth/token",
        user_info_url=f"{base_url.rstrip('/')}/kakao/kapi/v2/user/me",
    )
    try:
        profile = kakao.user_from_code("simulation-code")
    finally:
        kakao.close()
    assert profile.user_id == "simulation-user-1"
    assert profile.nickname == "Simulation Nickname"

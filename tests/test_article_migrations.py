import importlib

import jwt
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.core import security
from app.db.database import Base
from app.models.user import User


def _identity_dependencies():
    try:
        return importlib.import_module("app.api.dependencies")
    except ModuleNotFoundError as exc:
        pytest.fail(f"identity dependencies are missing: {exc}")


def test_current_user_resolves_email_and_kakao_subjects(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'identity.db'}")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(security.settings, "SECRET_KEY", "paid-article-test-secret-key-at-least-32-bytes")
    monkeypatch.setattr(security.settings, "ALGORITHM", "HS256")
    with Session(engine) as db:
        email_user = User(email="email@example.com", password="pw", name="Email")
        kakao_user = User(email=None, password=None, name="Kakao", kakao_user_id="k-1")
        db.add_all([email_user, kakao_user])
        db.commit()
        secret = security.settings.SECRET_KEY
        email_token = jwt.encode({"sub": email_user.email}, secret, algorithm="HS256")
        kakao_token = jwt.encode({"sub": "kakao:k-1"}, secret, algorithm="HS256")
        dependencies = _identity_dependencies()

        assert dependencies.get_current_user(db=db, token=email_token).idx == email_user.idx
        assert dependencies.get_current_user(db=db, token=kakao_token).idx == kakao_user.idx
    engine.dispose()


def test_current_user_rejects_invalid_or_expired_token(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'identity.db'}")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(security.settings, "SECRET_KEY", "paid-article-test-secret-key-at-least-32-bytes")
    monkeypatch.setattr(security.settings, "ALGORITHM", "HS256")
    with Session(engine) as db:
        dependencies = _identity_dependencies()
        expired = jwt.encode({"sub": "missing@example.com", "exp": 1}, security.settings.SECRET_KEY, algorithm="HS256")
        for token in ("tampered", expired):
            with pytest.raises(HTTPException) as error:
                dependencies.get_current_user(db=db, token=token)
            assert error.value.status_code == 401
    engine.dispose()


def test_optional_current_user_returns_none_for_anonymous_request(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'identity.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        dependencies = _identity_dependencies()
        assert dependencies.get_optional_current_user(db=db, token=None) is None
    engine.dispose()


def test_legacy_board_migration_preserves_posts_as_free(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE board (idx INTEGER PRIMARY KEY, title VARCHAR NOT NULL, "
            "contents VARCHAR NOT NULL, category VARCHAR(20))"
        ))
        connection.execute(text(
            "INSERT INTO board (idx, title, contents, category) "
            "VALUES (4, '이전 글', '본문 보존', '과학/IT')"
        ))

    try:
        ensure_board_sale_columns = importlib.import_module("app.db.database").ensure_board_sale_columns
    except AttributeError as exc:
        pytest.fail(f"sale schema migration is missing: {exc}")
    ensure_board_sale_columns(engine)
    ensure_board_sale_columns(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("board")}
    with engine.connect() as connection:
        row = connection.execute(text(
            "SELECT title, contents, category, author_idx, preview, sale_price "
            "FROM board WHERE idx = 4"
        )).one()
    assert {"author_idx", "preview", "sale_price"}.issubset(columns)
    assert tuple(row) == ("이전 글", "본문 보존", "과학/IT", None, None, None)
    engine.dispose()


def test_legacy_purchase_migration_leaves_payment_unverified(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'purchase.db'}")
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE purchase (id INTEGER PRIMARY KEY, buyer_idx INTEGER NOT NULL, "
            "board_idx INTEGER NOT NULL, price INTEGER NOT NULL, created_at DATETIME)"
        ))
        connection.execute(text(
            "INSERT INTO purchase (id, buyer_idx, board_idx, price) VALUES (1, 3, 8, 900)"
        ))
    migration = importlib.import_module("app.db.database").ensure_purchase_payment_column
    migration(engine)
    migration(engine)
    columns = {column["name"] for column in inspect(engine).get_columns("purchase")}
    with engine.connect() as connection:
        row = connection.execute(text("SELECT buyer_idx, board_idx, price, payment_id FROM purchase WHERE id = 1")).one()
    assert "payment_id" in columns
    assert tuple(row) == (3, 8, 900, None)
    engine.dispose()

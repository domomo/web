from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import Base, ensure_user_kakao_schema
from app.models.user import User


def _engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path / 'users.db'}")


def test_user_schema_migration_preserves_existing_local_account(tmp_path):
    engine = _engine(tmp_path)
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE user (idx INTEGER PRIMARY KEY, email VARCHAR NOT NULL, "
            "password VARCHAR NOT NULL, name VARCHAR NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO user (idx, email, password, name) "
            "VALUES (7, 'local@example.com', 'secret', 'Local')"
        ))

    ensure_user_kakao_schema(engine)

    with engine.connect() as connection:
        row = connection.execute(text(
            "SELECT idx, email, password, name, kakao_user_id FROM user"
        )).one()
    assert tuple(row) == (7, "local@example.com", "secret", "Local", None)
    columns = {column["name"]: column for column in inspect(engine).get_columns("user")}
    assert columns["email"]["nullable"]
    assert columns["password"]["nullable"]
    assert columns["kakao_user_id"]["nullable"]
    engine.dispose()


def test_new_user_schema_accepts_kakao_user_without_credentials(tmp_path):
    engine = _engine(tmp_path)
    Base.metadata.create_all(engine)
    ensure_user_kakao_schema(engine)
    with Session(engine) as session:
        session.add(User(email=None, password=None, name="Kakao", kakao_user_id="123"))
        session.commit()
        user = session.query(User).one()
        assert user.email is None and user.password is None
    engine.dispose()


def test_user_schema_enforces_unique_kakao_user_id(tmp_path):
    engine = _engine(tmp_path)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all([
            User(email=None, password=None, name="One", kakao_user_id="123"),
            User(email=None, password=None, name="Two", kakao_user_id="123"),
        ])
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("duplicate Kakao IDs must be rejected")
    engine.dispose()


def test_user_schema_migration_rolls_back_without_losing_existing_users(tmp_path):
    engine = _engine(tmp_path)
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE TABLE user (idx INTEGER PRIMARY KEY, email VARCHAR NOT NULL, "
            "password VARCHAR NOT NULL, name VARCHAR NOT NULL)"
        ))
        connection.execute(text(
            "INSERT INTO user VALUES (1, 'keep@example.com', 'pw', 'Keep')"
        ))

    from sqlalchemy import event

    def fail_create(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith('CREATE TABLE "user" ('):
            raise RuntimeError("injected migration failure")

    event.listen(engine, "before_cursor_execute", fail_create)
    try:
        try:
            ensure_user_kakao_schema(engine)
        except RuntimeError:
            pass
        else:
            raise AssertionError("migration failure should propagate")
    finally:
        event.remove(engine, "before_cursor_execute", fail_create)

    assert "user" in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.execute(text("SELECT email, name FROM user")).one() == (
            "keep@example.com", "Keep"
        )
    engine.dispose()

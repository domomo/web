# ORM : Object Relation Mapping
# 객체 : 현실 세상의 무언가를 컴퓨터 코드로 옮긴 것
# 개체 : 현실 세상의 무언가를 컴퓨터의 데이터로 옮긴 것

# DB 서버와 연결 설정하는 파일

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

# DB 연결을 관리하는 엔진
engine = create_engine(settings.DATABASE_URL, echo=False)
# DB 작업용 세션을 만드는 도구
SessionLocal = sessionmaker(autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db # return은 값을 반환하고 함수를 종료하지만, yield는 반환하고 함수를 일시 중지한다.
    finally:
        db.close()

# 모델들이 상속받을 부모 클래스
class Base(DeclarativeBase):
    # 모든 테이블이 가지는 속성을 지정
    pass


def ensure_board_category_column(bind=engine):
    """Add the nullable category column to databases created by older versions."""
    if "board" not in inspect(bind).get_table_names():
        return
    columns = {column["name"] for column in inspect(bind).get_columns("board")}
    if "category" not in columns:
        with bind.begin() as connection:
            connection.execute(text("ALTER TABLE board ADD COLUMN category VARCHAR(20)"))


def ensure_board_sale_columns(bind=engine):
    """Add nullable sale fields to legacy board tables, preserving old rows."""
    inspector = inspect(bind)
    if "board" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("board")}
    additions = {
        "author_idx": "INTEGER",
        "preview": "VARCHAR",
        "sale_price": "INTEGER",
    }
    missing = [(name, definition) for name, definition in additions.items() if name not in columns]
    if not missing:
        return
    with bind.begin() as connection:
        for name, definition in missing:
            connection.execute(text(f"ALTER TABLE board ADD COLUMN {name} {definition}"))


def ensure_purchase_payment_column(bind=engine):
    """Mark pre-PortOne purchase rows as unverified and add a payment reference."""
    inspector = inspect(bind)
    if "purchase" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("purchase")}
    if "payment_id" not in columns:
        with bind.begin() as connection:
            connection.execute(text("ALTER TABLE purchase ADD COLUMN payment_id VARCHAR(100)"))
    with bind.begin() as connection:
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_purchase_payment_id ON purchase (payment_id)"
        ))


def ensure_user_kakao_schema(bind=engine):
    """Rebuild legacy SQLite user tables to support Kakao-only accounts."""
    inspector = inspect(bind)
    if "user" not in inspector.get_table_names():
        return
    columns = {column["name"]: column for column in inspector.get_columns("user")}
    if (
        "kakao_user_id" in columns
        and columns["email"]["nullable"]
        and columns["password"]["nullable"]
    ):
        return

    # This migration is intentionally SQLite-specific; the project database is SQLite.
    if bind.dialect.name != "sqlite":
        raise RuntimeError("User Kakao schema migration requires SQLite")
    # SQLite's legacy transaction mode does not begin a transaction for DDL,
    # so start one explicitly before renaming the source table.
    connection = bind.connect()
    connection.exec_driver_sql("BEGIN IMMEDIATE")
    try:
        connection.execute(text('ALTER TABLE "user" RENAME TO "user_legacy_kakao"'))
        connection.execute(text(
            'CREATE TABLE "user" ('
            'idx INTEGER NOT NULL PRIMARY KEY, '
            'email VARCHAR, password VARCHAR, name VARCHAR NOT NULL, '
            'kakao_user_id VARCHAR, UNIQUE (kakao_user_id))'
        ))
        legacy_columns = set(columns)
        copy_columns = [name for name in ("idx", "email", "password", "name") if name in legacy_columns]
        joined = ", ".join(f'"{name}"' for name in copy_columns)
        connection.execute(text(
            f'INSERT INTO "user" ({joined}) SELECT {joined} FROM "user_legacy_kakao"'
        ))
        connection.execute(text('DROP TABLE "user_legacy_kakao"'))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


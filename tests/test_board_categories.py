import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, ensure_board_category_column, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autoflush=False, bind=engine)

    def override_get_db():
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_board_write_requires_a_supported_category(client):
    missing = client.post("/api/board/write", json={"title": "제목", "contents": "내용"})
    invalid = client.post(
        "/api/board/write",
        json={"title": "제목", "contents": "내용", "category": "기타"},
    )

    assert missing.status_code == 422
    assert invalid.status_code == 422


def test_board_write_read_and_aggregate_list_include_category(client):
    written = client.post(
        "/api/board/write",
        json={"title": "작은 발견", "contents": "새로 배운 것", "category": "과학/IT"},
    )

    assert written.status_code == 200
    assert written.json()["category"] == "과학/IT"
    idx = written.json()["idx"]
    assert client.get(f"/api/board/read/{idx}").json()["category"] == "과학/IT"
    assert client.get("/api/board/list").json()[0]["category"] == "과학/IT"


def test_board_list_filters_before_pagination_and_keeps_legacy_in_aggregate(client):
    from app.models.board import Board

    session_override = app.dependency_overrides[get_db]
    session_generator = session_override()
    session = next(session_generator)
    session.add_all(
        [
            Board(title="경제 오래된 글", contents="", category="경제/경영"),
            Board(title="분야 없는 옛 글", contents="", category=None),
            Board(title="경제 최신 글", contents="", category="경제/경영"),
            Board(title="과학 글", contents="", category="과학/IT"),
        ]
    )
    session.commit()
    session_generator.close()

    all_posts = client.get("/api/board/list").json()
    economy = client.get("/api/board/list", params={"category": "경제/경영", "offset": 1, "limit": 1}).json()
    legacy_in_category = client.get("/api/board/list", params={"category": "인문/교양"}).json()
    invalid_category = client.get("/api/board/list", params={"category": "기타"})

    assert len(all_posts) == 4
    assert all_posts[2]["category"] is None
    assert economy[0]["title"] == "경제 오래된 글"
    assert legacy_in_category == []
    assert invalid_category.status_code == 422


def test_existing_sqlite_board_gets_nullable_category_column():
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            text("CREATE TABLE board (idx INTEGER PRIMARY KEY, title VARCHAR NOT NULL, contents VARCHAR NOT NULL)")
        )
        connection.execute(text("INSERT INTO board (idx, title, contents) VALUES (1, '이전 노트', '내용')"))

    ensure_board_category_column(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("board")}
    with engine.connect() as connection:
        category = connection.execute(text("SELECT category FROM board WHERE idx = 1")).scalar_one()
    engine.dispose()

    assert "category" in columns
    assert category is None

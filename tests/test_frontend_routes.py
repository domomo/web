from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_vue_pages_can_be_opened_directly():
    for path in ("/signup", "/login", "/posts", "/posts/new", "/posts/42"):
        response = client.get(path)
        assert response.status_code == 200
        assert '<div id="app"></div>' in response.text


def test_unknown_api_path_remains_a_not_found_response():
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404

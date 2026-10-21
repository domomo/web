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


def test_backend_allows_the_deployed_frontend_origin_with_credentials():
    response = client.options(
        "/api/user/me",
        headers={
            "Origin": "https://www.aiready.p-e.kr",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://www.aiready.p-e.kr"
    assert response.headers["access-control-allow-credentials"] == "true"

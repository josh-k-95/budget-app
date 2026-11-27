from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def spa_client(tmp_path: Path) -> TestClient:
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>spa</html>")
    (dist / "assets" / "app.js").write_text("console.log('hi')")
    (tmp_path / "secret.txt").write_text("outside dist")
    settings = Settings(database_url="postgresql+psycopg://unused", frontend_dist=dist)
    return TestClient(create_app(settings))


def test_serves_index_at_root(spa_client: TestClient) -> None:
    response = spa_client.get("/")
    assert response.status_code == 200
    assert response.text == "<html>spa</html>"


def test_client_routes_fall_back_to_index(spa_client: TestClient) -> None:
    response = spa_client.get("/transactions/2026-11")
    assert response.status_code == 200
    assert response.text == "<html>spa</html>"


def test_serves_static_files(spa_client: TestClient) -> None:
    response = spa_client.get("/assets/app.js")
    assert response.status_code == 200
    assert "console.log" in response.text


def test_unknown_api_route_is_json_404(spa_client: TestClient) -> None:
    response = spa_client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_does_not_serve_files_outside_dist(spa_client: TestClient) -> None:
    response = spa_client.get("/..%2Fsecret.txt")
    assert "outside dist" not in response.text

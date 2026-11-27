from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import create_app


def test_config_defaults_app_name(client: TestClient) -> None:
    response = client.get("/api/config")
    assert response.status_code == 200
    assert response.json() == {"app_name": "Budget App"}


def test_config_reads_app_name_from_settings() -> None:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url="postgresql+psycopg://unused", app_name="Renamed"
    )
    assert TestClient(app).get("/api/config").json() == {"app_name": "Renamed"}

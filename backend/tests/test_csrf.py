import pytest
from fastapi.testclient import TestClient

from app.config import normalize_origin
from tests.conftest import make_client, make_settings

CREDS = {"username": "alice", "password": "correct horse battery"}


@pytest.mark.parametrize("origin", [None, "null", "http://evil.example", "http://localhost:5173"])
def test_state_changing_request_with_bad_origin_is_refused(origin: str | None) -> None:
    with make_client(origin=origin) as client:
        response = client.post("/api/auth/register", json=CREDS)
    assert response.status_code == 403
    assert response.json() == {"detail": "Origin not allowed"}


def test_matching_origin_is_allowed(client: TestClient) -> None:
    assert client.post("/api/auth/register", json=CREDS).status_code == 201


def test_get_requests_do_not_need_origin() -> None:
    with make_client(origin=None) as client:
        assert client.get("/api/config").status_code == 200


def test_logout_is_also_protected() -> None:
    with make_client(origin="http://evil.example") as client:
        assert client.post("/api/auth/logout").status_code == 403


def test_origin_comparison_normalises_case_and_default_ports() -> None:
    settings = make_settings(public_url="https://Budget.Example.test:443/some/path")
    origin = "https://budget.example.test"
    assert settings.public_origin == origin
    with make_client(settings, base_url=origin, origin="HTTPS://BUDGET.EXAMPLE.TEST") as client:
        assert client.post("/api/auth/register", json=CREDS).status_code == 201


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost:8000", "http://localhost:8000"),
        ("http://localhost:80/", "http://localhost"),
        ("https://x.test:8443", "https://x.test:8443"),
        ("http://[::1]:8000", "http://[::1]:8000"),
    ],
)
def test_normalize_origin(url: str, expected: str) -> None:
    assert normalize_origin(url) == expected


# --- plain-HTTP refusal -----------------------------------------------------------------


def test_login_over_plain_http_on_public_host_is_refused() -> None:
    settings = make_settings(public_url="http://budget.example.test")
    with make_client(
        settings, base_url="http://budget.example.test", origin="http://budget.example.test"
    ) as client:
        response = client.post("/api/auth/login", json=CREDS)
        assert response.status_code == 403
        assert response.json() == {"detail": "HTTPS is required to sign in"}
        assert client.post("/api/auth/register", json=CREDS).status_code == 403


def test_plain_http_allowed_when_explicitly_enabled() -> None:
    settings = make_settings(public_url="http://budget.example.test", allow_insecure_http=True)
    with make_client(
        settings, base_url="http://budget.example.test", origin="http://budget.example.test"
    ) as client:
        assert client.post("/api/auth/register", json=CREDS).status_code == 201


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "[::1]"])
def test_plain_http_allowed_on_localhost(host: str) -> None:
    url = f"http://{host}:8000"
    with make_client(make_settings(public_url=url), base_url=url, origin=url) as client:
        assert client.post("/api/auth/register", json=CREDS).status_code == 201


def test_https_forwarded_by_trusted_proxy_is_accepted() -> None:
    """Uvicorn's proxy-header middleware (as run in Docker) turns X-Forwarded-Proto into https."""
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

    from app.main import create_app

    public = "https://budget.example.test"
    app = ProxyHeadersMiddleware(
        create_app(make_settings(public_url=public)), trusted_hosts="10.0.0.1"
    )
    headers = {"Origin": public, "X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.5"}
    trusted = TestClient(app, base_url="http://budget.example.test", client=("10.0.0.1", 1234))
    assert trusted.post("/api/auth/register", json=CREDS, headers=headers).status_code == 201

    # The same header from an untrusted peer is ignored, so the plain-HTTP guard applies.
    untrusted = TestClient(app, base_url="http://budget.example.test", client=("10.9.9.9", 1234))
    response = untrusted.post("/api/auth/login", json=CREDS, headers=headers)
    assert response.status_code == 403

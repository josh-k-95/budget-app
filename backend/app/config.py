from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "static"


class Settings(BaseSettings):
    """All runtime configuration, read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    public_url: str = "http://localhost:8000"
    app_name: str = "Budget App"
    allow_signup: bool = True
    allow_insecure_http: bool = False
    min_password_length: int = 8
    frontend_dist: Path = DEFAULT_FRONTEND_DIST

    @property
    def public_origin(self) -> str:
        """`scheme://host[:port]` of PUBLIC_URL, normalised for Origin header comparison."""
        return normalize_origin(self.public_url)

    @property
    def secure_cookies(self) -> bool:
        return urlsplit(self.public_url).scheme == "https"


def normalize_origin(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    if ":" in host:  # IPv6 literal
        host = f"[{host}]"
    port = parts.port
    if port is None or (scheme, port) in {("http", 80), ("https", 443)}:
        return f"{scheme}://{host}"
    return f"{scheme}://{host}:{port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment

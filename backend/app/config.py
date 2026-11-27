from functools import lru_cache
from pathlib import Path

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


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from the environment

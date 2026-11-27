import os

# Tests run against a real Postgres (see `docker compose --profile test up -d db-test`).
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://budget:budget@localhost:5433/budget_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from collections.abc import Iterator  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import Engine, create_engine, inspect, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


def alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = TEST_DATABASE_URL
    config.attributes["configure_logger"] = False
    return config


def reset_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    engine = create_engine(TEST_DATABASE_URL)
    reset_schema(engine)
    command.upgrade(alembic_config(), "head")
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """A session whose work is rolled back after each test."""
    with engine.connect() as conn:
        trans = conn.begin()
        with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
            yield session
        trans.rollback()


@pytest.fixture(autouse=True)
def clean_db(engine: Engine) -> Iterator[None]:
    """API tests commit through the app, so wipe all data after each test."""
    yield
    tables = [t for t in inspect(engine).get_table_names() if t != "alembic_version"]
    if tables:
        with engine.begin() as conn:
            conn.execute(text(f"TRUNCATE {', '.join(tables)} CASCADE"))


LOCAL_URL = "http://localhost:8000"


def make_client(
    settings: Settings | None = None,
    base_url: str = LOCAL_URL,
    origin: str | None = LOCAL_URL,
    client_ip: str = "203.0.113.10",
) -> TestClient:
    """TestClient that looks like a same-origin browser on localhost by default."""
    headers = {"Origin": origin} if origin else {}
    return TestClient(
        create_app(settings), base_url=base_url, headers=headers, client=(client_ip, 50000)
    )


def make_settings(**overrides: object) -> Settings:
    return Settings(database_url=TEST_DATABASE_URL, **overrides)  # type: ignore[arg-type]


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    with make_client() as client:
        yield client

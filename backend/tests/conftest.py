from collections.abc import Iterator
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from gamedeck.config import AppSettings
from gamedeck.main import create_app


BACKEND_DIR = Path(__file__).resolve().parents[1]


def migrate_database(database_url: str) -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = database_url
    command.upgrade(config, "head")


@pytest.fixture
def migrated_database(tmp_path: Path) -> Iterator[tuple[Path, str]]:
    database_path = tmp_path / "gamedeck-test.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    migrate_database(database_url)
    yield database_path, database_url


@pytest.fixture
def api_client(
    migrated_database: tuple[Path, str], tmp_path: Path
) -> Iterator[TestClient]:
    _, database_url = migrated_database
    app = create_app(
        AppSettings(database_url=database_url, log_dir=tmp_path / "logs"),
        enable_monitor=False,
    )
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db_session(migrated_database: tuple[Path, str], tmp_path: Path) -> Iterator[Session]:
    _, database_url = migrated_database
    app = create_app(
        AppSettings(database_url=database_url, log_dir=tmp_path / "logs"),
        enable_monitor=False,
    )
    database = app.state.database
    session = database.session_factory()
    try:
        yield session
    finally:
        session.close()
        database.dispose()

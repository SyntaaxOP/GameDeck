from pathlib import Path

from sqlalchemy import text

from gamedeck.config import AppSettings
from gamedeck.db import Database


def test_sqlite_connections_enable_safety_pragmas(tmp_path: Path) -> None:
    database = Database(
        AppSettings(
            database_url=f"sqlite:///{(tmp_path / 'pragmas.db').as_posix()}",
            log_dir=tmp_path / "logs",
            sqlite_busy_timeout_ms=7_500,
        )
    )

    try:
        with database.engine.connect() as connection:
            foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
            journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()
            busy_timeout = connection.execute(text("PRAGMA busy_timeout")).scalar_one()
    finally:
        database.dispose()

    assert foreign_keys == 1
    assert journal_mode.lower() == "wal"
    assert busy_timeout == 7_500


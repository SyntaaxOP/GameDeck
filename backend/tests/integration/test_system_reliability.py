from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient

from gamedeck.config import AppSettings
from gamedeck.main import create_app


def test_verified_online_backup_and_diagnostics(
    migrated_database: tuple[Path, str], tmp_path: Path
) -> None:
    database_path, database_url = migrated_database
    backup_dir = tmp_path / "backups"
    app = create_app(
        AppSettings(
            database_url=database_url,
            log_dir=tmp_path / "logs",
            backup_dir=backup_dir,
        ),
        enable_monitor=False,
    )
    with TestClient(app) as client:
        created = client.post("/api/v1/games", json={
            "title": "Hades", "platform": "steam", "executable_name": "hades.exe"
        })
        backup = client.post("/api/v1/system/backups")
        diagnostics = client.get("/api/v1/system/diagnostics")
        listed = client.get("/api/v1/system/backups")

    assert created.status_code == 201
    assert backup.status_code == 201, backup.text
    backup_path = Path(backup.json()["path"])
    assert backup_path.parent == backup_dir.resolve()
    assert backup.json()["integrity_check"] == "ok"
    with sqlite3.connect(backup_path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("SELECT count(*) FROM games").fetchone()[0] == 1
    assert diagnostics.status_code == 200
    assert diagnostics.json()["database_path"] == str(database_path.resolve())
    assert diagnostics.json()["database_integrity"] == "ok"
    assert diagnostics.json()["database_journal_mode"].lower() == "wal"
    assert diagnostics.json()["database_probe_ms"] < 1_000
    assert diagnostics.json()["game_count"] == 1
    assert listed.json()[0]["filename"] == backup.json()["filename"]


def test_database_lock_exhaustion_returns_retryable_error(
    migrated_database: tuple[Path, str], tmp_path: Path
) -> None:
    database_path, database_url = migrated_database
    app = create_app(
        AppSettings(
            database_url=database_url,
            log_dir=tmp_path / "logs",
            backup_dir=tmp_path / "backups",
            sqlite_busy_timeout_ms=25,
        ),
        enable_monitor=False,
    )
    lock = sqlite3.connect(database_path, isolation_level=None)
    try:
        lock.execute("BEGIN IMMEDIATE")
        with TestClient(app) as client:
            response = client.post("/api/v1/games", json={
                "title": "Hades", "platform": "steam", "executable_name": "hades.exe"
            })
    finally:
        lock.rollback()
        lock.close()

    assert response.status_code == 503
    assert response.headers["retry-after"] == "1"
    assert response.json()["error"]["code"] == "database_busy"
    assert "locked" not in response.text.lower()


def test_corrupted_json_returns_stable_validation_error(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/games",
        content=b'{"title":',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["message"] == "The request contains invalid fields."

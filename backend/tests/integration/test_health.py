from pathlib import Path

from fastapi.testclient import TestClient

from gamedeck.config import AppSettings
from gamedeck.main import create_app


def test_health_reports_application_and_database_ready(tmp_path: Path) -> None:
    settings = AppSettings(
        database_url=f"sqlite:///{(tmp_path / 'health.db').as_posix()}",
        log_dir=tmp_path / "logs",
    )
    app = create_app(settings, enable_monitor=False)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "ready",
        "version": "0.8.3",
    }

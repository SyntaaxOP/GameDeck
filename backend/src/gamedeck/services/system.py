"""Local backup and diagnostics operations."""

from datetime import UTC, datetime
from pathlib import Path
import sqlite3
import time

from sqlalchemy import func, select, text

from gamedeck.config import AppSettings
from gamedeck.db import Database
from gamedeck.domain.errors import DomainError
from gamedeck.models.game import Game
from gamedeck.models.game_session import GameSession
from gamedeck.models.purchase import Purchase
from gamedeck.schemas.system import BackupResponse, DiagnosticsResponse


class BackupUnavailableError(DomainError):
    code = "backup_unavailable"
    status_code = 409


class SystemService:
    def __init__(self, database: Database, settings: AppSettings) -> None:
        self.database = database
        self.settings = settings

    def create_backup(self) -> BackupResponse:
        if self.database.engine.url.get_backend_name() != "sqlite":
            raise BackupUnavailableError("Online backups are available only for SQLite databases.")
        self.settings.backup_dir.mkdir(parents=True, exist_ok=True)
        created_at = datetime.now(UTC)
        filename = f"gamedeck-{created_at.strftime('%Y%m%d-%H%M%S-%f')}.db"
        destination = (self.settings.backup_dir / filename).resolve()
        temporary = destination.with_suffix(".tmp")
        raw = self.database.engine.raw_connection()
        target: sqlite3.Connection | None = None
        try:
            source = raw.driver_connection
            target = sqlite3.connect(temporary)
            source.backup(target)
            cursor = target.execute("PRAGMA integrity_check")
            try:
                integrity = str(cursor.fetchone()[0])
            finally:
                cursor.close()
            target.close()
            target = None
            if integrity.lower() != "ok":
                temporary.unlink(missing_ok=True)
                raise BackupUnavailableError("SQLite rejected the backup integrity check.")
            temporary.replace(destination)
        except (sqlite3.Error, OSError) as exc:
            if target is not None:
                target.close()
                target = None
            temporary.unlink(missing_ok=True)
            raise BackupUnavailableError("GameDeck could not create a verified backup.") from exc
        finally:
            if target is not None:
                target.close()
            raw.close()
        return BackupResponse(
            filename=filename,
            path=str(destination),
            size_bytes=destination.stat().st_size,
            created_at=created_at,
            integrity_check="ok",
        )

    def list_backups(self) -> list[BackupResponse]:
        if not self.settings.backup_dir.exists():
            return []
        results = []
        for path in sorted(self.settings.backup_dir.glob("gamedeck-*.db"), reverse=True):
            stat = path.stat()
            results.append(BackupResponse(
                filename=path.name,
                path=str(path.resolve()),
                size_bytes=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_mtime, UTC),
                integrity_check="not_rechecked",
            ))
        return results

    def diagnostics(self) -> DiagnosticsResponse:
        database_path = self.database.sqlite_path()
        started = time.perf_counter()
        with self.database.engine.connect() as connection:
            journal_mode = str(connection.execute(text("PRAGMA journal_mode")).scalar_one())
            integrity = str(connection.execute(text("PRAGMA quick_check")).scalar_one())
            game_count = int(connection.execute(select(func.count()).select_from(Game)).scalar_one())
            session_count = int(connection.execute(select(func.count()).select_from(GameSession)).scalar_one())
            purchase_count = int(connection.execute(select(func.count()).select_from(Purchase)).scalar_one())
        probe_ms = round((time.perf_counter() - started) * 1_000, 2)
        log_path = (self.settings.log_dir / "gamedeck.log").resolve()
        return DiagnosticsResponse(
            database_path=str(database_path),
            database_size_bytes=self._size(database_path),
            wal_size_bytes=self._size(Path(f"{database_path}-wal")),
            log_path=str(log_path),
            log_size_bytes=self._size(log_path),
            backup_directory=str(self.settings.backup_dir.resolve()),
            sqlite_busy_timeout_ms=self.settings.sqlite_busy_timeout_ms,
            database_journal_mode=journal_mode,
            database_integrity=integrity,
            database_probe_ms=probe_ms,
            game_count=game_count,
            session_count=session_count,
            purchase_count=purchase_count,
        )

    @staticmethod
    def _size(path: Path) -> int:
        return path.stat().st_size if path.exists() else 0

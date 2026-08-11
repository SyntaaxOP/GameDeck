"""Operational diagnostics and backup contracts."""

from datetime import datetime

from pydantic import BaseModel


class BackupResponse(BaseModel):
    filename: str
    path: str
    size_bytes: int
    created_at: datetime
    integrity_check: str


class DiagnosticsResponse(BaseModel):
    database_path: str
    database_size_bytes: int
    wal_size_bytes: int
    log_path: str
    log_size_bytes: int
    backup_directory: str
    sqlite_busy_timeout_ms: int
    database_journal_mode: str
    database_integrity: str
    database_probe_ms: float
    game_count: int
    session_count: int
    purchase_count: int

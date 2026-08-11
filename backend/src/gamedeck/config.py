"""Typed local application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class AppSettings(BaseSettings):
    """Configuration loaded from GAMEDECK_* environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="GAMEDECK_",
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GameDeck"
    environment: str = "development"
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'data' / 'gamedeck.db').as_posix()}"
    log_level: str = "INFO"
    log_dir: Path = BACKEND_DIR / "logs"
    backup_dir: Path = BACKEND_DIR / "backups"
    artwork_dir: Path = BACKEND_DIR / "data" / "artwork"
    sql_echo: bool = False
    sqlite_busy_timeout_ms: int = Field(default=5_000, ge=0, le=60_000)
    steam_api_key: SecretStr | None = None
    steam_id: str | None = Field(default=None, pattern=r"^\d{17}$")
    steam_path: Path | None = None


@lru_cache
def get_settings() -> AppSettings:
    """Return the process-wide immutable settings instance."""

    return AppSettings()

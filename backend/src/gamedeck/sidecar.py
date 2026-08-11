"""Packaged desktop entry point using per-user Windows data paths."""
from __future__ import annotations
import os
from pathlib import Path
import sys

def configure_data() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "GameDeck"
    base.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("GAMEDECK_DATABASE_URL", f"sqlite:///{(base / 'gamedeck.db').as_posix()}")
    os.environ.setdefault("GAMEDECK_LOG_DIR", str(base / "logs"))
    os.environ.setdefault("GAMEDECK_BACKUP_DIR", str(base / "backups"))
    os.environ.setdefault("GAMEDECK_ARTWORK_DIR", str(base / "artwork"))
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))

def main() -> None:
    root = configure_data()
    from alembic import command
    from alembic.config import Config
    import uvicorn
    config = Config(str(root / "alembic.ini"))
    command.upgrade(config, "head")
    uvicorn.run("gamedeck.main:app", host="127.0.0.1", port=8000, workers=1, log_level="warning")

if __name__ == "__main__": main()

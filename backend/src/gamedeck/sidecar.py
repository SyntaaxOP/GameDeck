"""Packaged desktop entry point using per-user Windows data paths."""
from __future__ import annotations
import os
from pathlib import Path
import sys

def configure_data() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "GameDeck"
    base.mkdir(parents=True, exist_ok=True)
    log_dir = Path(os.environ.get("GAMEDECK_LOG_DIR", base / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    if sys.stdout is None or sys.stderr is None:
        stream = (log_dir / "sidecar-bootstrap.log").open("a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or stream
        sys.stderr = sys.stderr or stream
    os.environ.setdefault("GAMEDECK_DATABASE_URL", f"sqlite:///{(base / 'gamedeck.db').as_posix()}")
    os.environ.setdefault("GAMEDECK_LOG_DIR", str(log_dir))
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
    port = int(os.environ.get("GAMEDECK_PORT", "8000"))
    uvicorn.run("gamedeck.main:app", host="127.0.0.1", port=port, workers=1, log_level="warning")

if __name__ == "__main__": main()

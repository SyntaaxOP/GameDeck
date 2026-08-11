"""Application logging setup."""

from logging.config import dictConfig
from pathlib import Path


def configure_logging(log_level: str, log_dir: Path) -> None:
    """Configure concise console logs and a bounded local log file."""

    log_dir.mkdir(parents=True, exist_ok=True)
    level = log_level.upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": level,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(log_dir / "gamedeck.log"),
                    "maxBytes": 2_000_000,
                    "backupCount": 3,
                    "encoding": "utf-8",
                    "formatter": "standard",
                    "level": level,
                },
            },
            "root": {"handlers": ["console", "file"], "level": level},
            "loggers": {
                "uvicorn.access": {
                    "handlers": ["console", "file"],
                    "level": level,
                    "propagate": False,
                }
            },
        }
    )


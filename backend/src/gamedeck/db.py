"""SQLAlchemy engine and session lifecycle."""

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from gamedeck.config import AppSettings


class Base(DeclarativeBase):
    """Base class for ORM models."""


def _ensure_sqlite_parent(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return
    Path(url.database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _configure_sqlite(engine: Engine, busy_timeout_ms: int) -> None:
    if engine.url.get_backend_name() != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={busy_timeout_ms:d}")
            cursor.execute("PRAGMA journal_mode=WAL")
        finally:
            cursor.close()


class Database:
    """Own the engine and session factory for one application instance."""

    def __init__(self, settings: AppSettings) -> None:
        _ensure_sqlite_parent(settings.database_url)
        connect_args = (
            {"check_same_thread": False}
            if make_url(settings.database_url).get_backend_name() == "sqlite"
            else {}
        )
        self.engine = create_engine(
            settings.database_url,
            echo=settings.sql_echo,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        _configure_sqlite(self.engine, settings.sqlite_busy_timeout_ms)
        self.session_factory = sessionmaker(
            bind=self.engine,
            class_=Session,
            autoflush=False,
            expire_on_commit=False,
        )

    def session(self) -> Iterator[Session]:
        db_session = self.session_factory()
        try:
            yield db_session
        finally:
            db_session.close()

    def is_ready(self) -> bool:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    def sqlite_path(self) -> Path:
        url = make_url(str(self.engine.url))
        if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
            raise ValueError("This database does not have a local SQLite file.")
        return Path(url.database).expanduser().resolve()

    def dispose(self) -> None:
        self.engine.dispose()

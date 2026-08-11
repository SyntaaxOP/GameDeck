"""Game library model."""

from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gamedeck.db import Base


class Game(Base):
    __tablename__ = "games"
    __table_args__ = (
        CheckConstraint(
            "platform IN ('steam', 'xbox', 'epic', 'fivem', 'local', 'emulator', 'other')",
            name="ck_games_platform",
        ),
        CheckConstraint(
            "status IN ('currently_playing', 'backlog', 'completed', "
            "'completed_100', 'dropped', 'paused')",
            name="ck_games_status",
        ),
        CheckConstraint("priority IS NULL OR priority BETWEEN 1 AND 5", name="ck_games_priority"),
        CheckConstraint(
            "personal_rating IS NULL OR personal_rating BETWEEN 1 AND 10",
            name="ck_games_personal_rating",
        ),
        Index("ix_games_status_archived", "status", "archived_at"),
        Index("ix_games_favorite_archived", "favorite", "archived_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False)
    executable_name: Mapped[str] = mapped_column(String(255), nullable=False)
    executable_path: Mapped[str | None] = mapped_column(Text)
    steam_app_id: Mapped[int | None] = mapped_column(Integer, unique=True)
    install_directory: Mapped[str | None] = mapped_column(Text)
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime)
    cover_path: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="backlog")
    priority: Mapped[int | None] = mapped_column(Integer)
    personal_rating: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    date_added: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_completed: Mapped[date | None] = mapped_column(Date)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    sessions: Mapped[list["GameSession"]] = relationship(back_populates="game")  # noqa: F821
    purchases: Mapped[list["Purchase"]] = relationship(back_populates="game")  # noqa: F821
    executable_mappings: Mapped[list["GameExecutable"]] = relationship(  # noqa: F821
        back_populates="game", cascade="all, delete-orphan", order_by="GameExecutable.id"
    )

    @property
    def executable_aliases(self) -> list["GameExecutable"]:  # noqa: F821
        return [mapping for mapping in self.executable_mappings if not mapping.is_primary]

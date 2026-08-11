"""Recorded gaming session model."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gamedeck.db import Base


class GameSession(Base):
    __tablename__ = "game_sessions"
    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_game_sessions_end_after_start",
        ),
        CheckConstraint(
            "last_seen_at >= started_at",
            name="ck_game_sessions_last_seen_after_start",
        ),
        CheckConstraint(
            "(ended_at IS NULL AND duration_seconds IS NULL) OR "
            "(ended_at IS NOT NULL AND duration_seconds IS NOT NULL)",
            name="ck_game_sessions_completion_state",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_game_sessions_duration_nonnegative",
        ),
        CheckConstraint(
            "detection_method IN ('process', 'manual', 'recovered')",
            name="ck_game_sessions_detection_method",
        ),
        CheckConstraint(
            "end_reason IS NULL OR end_reason IN "
            "('process_stopped', 'tracker_shutdown', 'recovered', 'manual')",
            name="ck_game_sessions_end_reason",
        ),
        Index("ix_game_sessions_game_started", "game_id", "started_at"),
        Index("ix_game_sessions_started_ended", "started_at", "ended_at"),
        Index("ix_game_sessions_ended_at", "ended_at"),
        Index(
            "uq_game_sessions_active_game",
            "game_id",
            unique=True,
            sqlite_where=text("ended_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="RESTRICT"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    detection_method: Mapped[str] = mapped_column(String(20), nullable=False)
    end_reason: Mapped[str | None] = mapped_column(String(30))
    process_id: Mapped[int | None] = mapped_column(Integer)
    process_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    game: Mapped["Game"] = relationship(back_populates="sessions")  # noqa: F821

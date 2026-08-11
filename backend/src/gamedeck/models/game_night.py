"""Local game-night planning models."""

from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from gamedeck.db import Base


class GameNight(Base):
    __tablename__ = "game_nights"
    __table_args__ = (
        CheckConstraint("status IN ('planned', 'completed', 'cancelled')", name="ck_game_nights_status"),
        CheckConstraint("duration_minutes BETWEEN 30 AND 720", name="ck_game_nights_duration"),
        Index("ix_game_nights_scheduled_status", "scheduled_at", "status"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    game_id: Mapped[int | None] = mapped_column(ForeignKey("games.id", ondelete="SET NULL"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, server_default="120")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="planned")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    game: Mapped["Game | None"] = relationship()  # noqa: F821
    attendees: Mapped[list["GameNightAttendee"]] = relationship(back_populates="game_night", cascade="all, delete-orphan", order_by="GameNightAttendee.id")


class GameNightAttendee(Base):
    __tablename__ = "game_night_attendees"
    __table_args__ = (
        CheckConstraint("response IN ('confirmed', 'maybe', 'declined')", name="ck_game_night_attendees_response"),
        Index("uq_game_night_attendees_name_ci", "game_night_id", text("lower(name)"), unique=True),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_night_id: Mapped[int] = mapped_column(ForeignKey("game_nights.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    response: Mapped[str] = mapped_column(String(20), nullable=False)
    game_night: Mapped[GameNight] = relationship(back_populates="attendees")

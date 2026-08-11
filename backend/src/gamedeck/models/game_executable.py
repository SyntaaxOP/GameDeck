"""Executable mappings used to identify a game process."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gamedeck.db import Base


class GameExecutable(Base):
    __tablename__ = "game_executables"
    __table_args__ = (
        Index(
            "uq_game_executables_active_name_ci",
            text("lower(executable_name)"),
            unique=True,
            sqlite_where=text("active = 1"),
        ),
        Index(
            "uq_game_executables_primary_game",
            "game_id",
            unique=True,
            sqlite_where=text("is_primary = 1"),
        ),
        Index("ix_game_executables_game", "game_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    executable_name: Mapped[str] = mapped_column(String(255), nullable=False)
    executable_path: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    game: Mapped["Game"] = relationship(back_populates="executable_mappings")  # noqa: F821

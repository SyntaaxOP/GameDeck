"""Manually curated FiveM server record."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from gamedeck.db import Base


class FiveMServer(Base):
    __tablename__ = "fivem_servers"
    __table_args__ = (
        CheckConstraint("tracked_playtime_seconds >= 0", name="ck_fivem_servers_playtime_nonnegative"),
        Index("uq_fivem_servers_address_ci", text("lower(address)"), unique=True),
        Index("ix_fivem_servers_favorite_last_joined", "favorite", "last_joined_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    connect_code: Mapped[str | None] = mapped_column(String(100))
    discord_url: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("0"))
    last_joined_at: Mapped[datetime | None] = mapped_column(DateTime)
    tracked_playtime_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

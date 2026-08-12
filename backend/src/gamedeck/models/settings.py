"""Single-user application settings model."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from gamedeck.db import Base


class Settings(Base):
    __tablename__ = "settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_settings_singleton"),
        CheckConstraint(
            "scan_interval_seconds BETWEEN 2 AND 60",
            name="ck_settings_scan_interval",
        ),
        CheckConstraint(
            "restart_grace_seconds BETWEEN 0 AND 120",
            name="ck_settings_restart_grace",
        ),
        CheckConstraint("week_starts_on BETWEEN 0 AND 6", name="ck_settings_week_start"),
        CheckConstraint("theme IN ('dark', 'light', 'system')", name="ck_settings_theme"),
        CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_settings_currency_code",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    scan_interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    restart_grace_seconds: Mapped[int] = mapped_column(Integer, nullable=False, server_default="15")
    tracking_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    week_starts_on: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    time_zone: Mapped[str] = mapped_column(String(100), nullable=False, server_default="UTC")
    time_zone_auto: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    theme: Mapped[str] = mapped_column(String(10), nullable=False, server_default="dark")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, server_default="PHP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

"""Application settings and tracker status schemas."""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator


class SettingsUpdate(BaseModel):
    scan_interval_seconds: int | None = Field(default=None, ge=2, le=60)
    restart_grace_seconds: int | None = Field(default=None, ge=0, le=120)
    tracking_enabled: bool | None = None
    week_starts_on: int | None = Field(default=None, ge=0, le=6)
    time_zone: str | None = Field(default=None, min_length=1, max_length=100)
    theme: str | None = Field(default=None, pattern="^(dark|light|system)$")
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)

    @field_validator("time_zone")
    @classmethod
    def validate_time_zone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Unknown IANA time zone.") from exc
        return value

    @field_validator("currency_code")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None


class SettingsResponse(BaseModel):
    scan_interval_seconds: int
    restart_grace_seconds: int
    tracking_enabled: bool
    week_starts_on: int
    time_zone: str
    theme: str
    currency_code: str
    updated_at: datetime


class TrackerStatusResponse(BaseModel):
    running: bool
    enabled: bool
    last_successful_scan_at: datetime | None
    last_error: str | None
    active_game_ids: list[int]
    scan_interval_seconds: int
    restart_grace_seconds: int

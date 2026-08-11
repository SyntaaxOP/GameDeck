"""Gaming session API schemas."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class DetectionMethod(StrEnum):
    PROCESS = "process"
    MANUAL = "manual"
    RECOVERED = "recovered"


class EndReason(StrEnum):
    PROCESS_STOPPED = "process_stopped"
    TRACKER_SHUTDOWN = "tracker_shutdown"
    RECOVERED = "recovered"
    MANUAL = "manual"


def require_aware_datetime(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include a UTC offset or timezone.")
    return value


class ManualSessionCreate(BaseModel):
    game_id: int = Field(gt=0)
    started_at: datetime
    ended_at: datetime

    @field_validator("started_at", "ended_at")
    @classmethod
    def validate_timezone(cls, value: datetime) -> datetime:
        return require_aware_datetime(value)

    @model_validator(mode="after")
    def validate_range(self) -> "ManualSessionCreate":
        if self.ended_at <= self.started_at:
            raise ValueError("Session end must be later than its start.")
        return self


class SessionUpdate(BaseModel):
    started_at: datetime | None = None
    ended_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, value: object) -> object:
        if isinstance(value, dict):
            null_fields = [field for field in ("started_at", "ended_at") if field in value and value[field] is None]
            if null_fields:
                raise ValueError(f"These fields cannot be null: {', '.join(null_fields)}.")
        return value

    @field_validator("started_at", "ended_at")
    @classmethod
    def validate_timezone(cls, value: datetime | None) -> datetime | None:
        return require_aware_datetime(value) if value is not None else None


class SessionResponse(BaseModel):
    id: int
    game_id: int
    game_title: str
    started_at: datetime
    ended_at: datetime | None
    last_seen_at: datetime
    duration_seconds: int | None
    detection_method: DetectionMethod
    end_reason: EndReason | None
    active: bool
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int
    page: int
    page_size: int


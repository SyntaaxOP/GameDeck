"""Local game-night contracts."""
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, field_validator, model_validator

class GameNightStatus(StrEnum): PLANNED="planned"; COMPLETED="completed"; CANCELLED="cancelled"
class AttendeeResponse(StrEnum): CONFIRMED="confirmed"; MAYBE="maybe"; DECLINED="declined"

class AttendeeInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    response: AttendeeResponse = AttendeeResponse.CONFIRMED
    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str: return value.strip()

class AttendeeResponseModel(AttendeeInput): id: int

class GameNightFields(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    game_id: int | None = Field(default=None, gt=0)
    scheduled_at: datetime
    duration_minutes: int = Field(default=120, ge=30, le=720)
    status: GameNightStatus = GameNightStatus.PLANNED
    notes: str | None = Field(default=None, max_length=10000)
    attendees: list[AttendeeInput] = Field(default_factory=list, max_length=50)
    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str: return value.strip()
    @field_validator("notes")
    @classmethod
    def trim_notes(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None
    @model_validator(mode="after")
    def unique_attendees(self):
        names=[item.name.casefold() for item in self.attendees]
        if len(names)!=len(set(names)): raise ValueError("Attendee names must be unique.")
        return self

class GameNightCreate(GameNightFields): pass
class GameNightUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200); game_id: int | None = Field(default=None, gt=0)
    scheduled_at: datetime | None = None; duration_minutes: int | None = Field(default=None, ge=30, le=720)
    status: GameNightStatus | None = None; notes: str | None = Field(default=None, max_length=10000); attendees: list[AttendeeInput] | None = Field(default=None, max_length=50)

class GameNightResponse(GameNightFields):
    id: int; game_title: str | None; attendees: list[AttendeeResponseModel]; created_at: datetime; updated_at: datetime
class GameNightListResponse(BaseModel): items: list[GameNightResponse]; total: int
class DiscordAnnouncementResponse(BaseModel): message: str

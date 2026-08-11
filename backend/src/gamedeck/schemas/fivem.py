"""FiveM companion API contracts."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


def optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class FiveMServerFields(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=255)
    connect_code: str | None = Field(default=None, max_length=100)
    discord_url: str | None = Field(default=None, max_length=2048)
    notes: str | None = Field(default=None, max_length=10000)
    favorite: bool = False
    last_joined_at: datetime | None = None
    tracked_playtime_seconds: int = Field(default=0, ge=0)

    @field_validator("name", "address")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required.")
        return value

    @field_validator("connect_code", "discord_url", "notes")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        return optional_text(value)

    @field_validator("discord_url")
    @classmethod
    def discord_link_only(cls, value: str | None) -> str | None:
        if value and not (value.startswith("https://discord.gg/") or value.startswith("https://discord.com/")):
            raise ValueError("Discord link must use discord.gg or discord.com over HTTPS.")
        return value


class FiveMServerCreate(FiveMServerFields):
    pass


class FiveMServerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, min_length=1, max_length=255)
    connect_code: str | None = Field(default=None, max_length=100)
    discord_url: str | None = Field(default=None, max_length=2048)
    notes: str | None = Field(default=None, max_length=10000)
    favorite: bool | None = None
    last_joined_at: datetime | None = None
    tracked_playtime_seconds: int | None = Field(default=None, ge=0)

    @field_validator("name", "address")
    @classmethod
    def trim_required(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("connect_code", "discord_url", "notes")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        return optional_text(value)


class FiveMServerResponse(FiveMServerFields):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class FiveMServerListResponse(BaseModel):
    items: list[FiveMServerResponse]
    total: int

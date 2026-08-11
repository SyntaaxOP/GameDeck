"""Game library API schemas."""

from datetime import date, datetime
from enum import StrEnum
from pathlib import PureWindowsPath

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Platform(StrEnum):
    STEAM = "steam"
    XBOX = "xbox"
    EPIC = "epic"
    FIVEM = "fivem"
    LOCAL = "local"
    EMULATOR = "emulator"
    OTHER = "other"


class LibraryStatus(StrEnum):
    CURRENTLY_PLAYING = "currently_playing"
    BACKLOG = "backlog"
    COMPLETED = "completed"
    COMPLETED_100 = "completed_100"
    DROPPED = "dropped"
    PAUSED = "paused"


class GameSort(StrEnum):
    TITLE = "title"
    DATE_ADDED = "date_added"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    PRIORITY = "priority"
    PLAY_NEXT = "play_next"


def normalize_executable_name(value: str) -> str:
    normalized = value.strip().lower()
    if not normalized:
        raise ValueError("Executable name is required.")
    if "/" in normalized or "\\" in normalized:
        raise ValueError("Use only the executable filename, for example game.exe.")
    if not normalized.endswith(".exe"):
        raise ValueError("Executable name must end with .exe.")
    return normalized


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


class ExecutableAliasInput(BaseModel):
    executable_name: str = Field(min_length=1, max_length=255)
    executable_path: str | None = Field(default=None, max_length=2_048)
    steam_app_id: int | None = Field(default=None, gt=0)

    @field_validator("executable_name")
    @classmethod
    def validate_executable_name(cls, value: str) -> str:
        return normalize_executable_name(value)

    @field_validator("executable_path")
    @classmethod
    def validate_executable_path(cls, value: str | None) -> str | None:
        value = normalize_optional_text(value)
        return validate_windows_path(value, field_name="Alias executable path")

    @model_validator(mode="after")
    def path_matches_name(self) -> "ExecutableAliasInput":
        if self.executable_path and PureWindowsPath(self.executable_path).name.lower() != self.executable_name:
            raise ValueError("Alias path filename must match its executable name.")
        return self


class ExecutableAliasResponse(ExecutableAliasInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GameFields(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    platform: Platform
    executable_name: str = Field(min_length=1, max_length=255)
    executable_path: str | None = Field(default=None, max_length=2_048)
    steam_app_id: int | None = Field(default=None, gt=0)
    install_directory: str | None = Field(default=None, max_length=2_048)
    discovered_at: datetime | None = None
    cover_path: str | None = Field(default=None, max_length=2_048)
    genre: str | None = Field(default=None, max_length=100)
    status: LibraryStatus = LibraryStatus.BACKLOG
    priority: int | None = Field(default=None, ge=1, le=5)
    personal_rating: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = Field(default=None, max_length=10_000)
    favorite: bool = False
    date_completed: date | None = None
    executable_aliases: list[ExecutableAliasInput] = Field(default_factory=list, max_length=10)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title is required.")
        return value

    @field_validator("executable_name")
    @classmethod
    def validate_executable_name(cls, value: str) -> str:
        return normalize_executable_name(value)

    @field_validator("executable_path", "install_directory", "cover_path", "genre", "notes")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)

    @model_validator(mode="after")
    def executable_names_are_distinct(self) -> "GameFields":
        names = [self.executable_name, *(alias.executable_name for alias in self.executable_aliases)]
        if len(names) != len(set(names)):
            raise ValueError("Primary and alias executable names must be distinct.")
        return self


class GameCreate(GameFields):
    pass


class GameUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    platform: Platform | None = None
    executable_name: str | None = Field(default=None, min_length=1, max_length=255)
    executable_path: str | None = Field(default=None, max_length=2_048)
    cover_path: str | None = Field(default=None, max_length=2_048)
    genre: str | None = Field(default=None, max_length=100)
    status: LibraryStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    personal_rating: int | None = Field(default=None, ge=1, le=10)
    notes: str | None = Field(default=None, max_length=10_000)
    favorite: bool | None = None
    date_completed: date | None = None
    executable_aliases: list[ExecutableAliasInput] | None = Field(default=None, max_length=10)
    install_directory: str | None = Field(default=None, max_length=2_048)

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, value: object) -> object:
        if isinstance(value, dict):
            required_fields = ("title", "platform", "executable_name", "status")
            null_fields = [field for field in required_fields if field in value and value[field] is None]
            if null_fields:
                raise ValueError(f"These fields cannot be null: {', '.join(null_fields)}.")
        return value

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Title is required.")
        return value

    @field_validator("executable_name")
    @classmethod
    def validate_executable_name(cls, value: str | None) -> str | None:
        return normalize_executable_name(value) if value is not None else None

    @field_validator("executable_path", "install_directory", "cover_path", "genre", "notes")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        return normalize_optional_text(value)


class GameResponse(GameFields):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_added: datetime
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    executable_aliases: list[ExecutableAliasResponse]


class GameListResponse(BaseModel):
    items: list[GameResponse]
    total: int
    page: int
    page_size: int


def validate_windows_path(path: str | None, *, field_name: str) -> str | None:
    if path is None:
        return None
    windows_path = PureWindowsPath(path)
    if not windows_path.is_absolute():
        raise ValueError(f"{field_name} must be an absolute Windows path.")
    return str(windows_path)

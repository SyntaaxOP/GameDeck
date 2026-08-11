"""Purchase ledger and spending analytics schemas."""

from datetime import UTC, date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PurchaseKind(StrEnum):
    BASE_GAME = "base_game"
    DLC = "dlc"
    SUBSCRIPTION = "subscription"
    OTHER = "other"


class PurchaseFields(BaseModel):
    game_id: int | None = Field(default=None, gt=0)
    kind: PurchaseKind
    amount_minor: int = Field(ge=0, le=2_147_483_647)
    currency_code: str = Field(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$")
    purchased_on: date | None = None
    platform: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("currency_code")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("platform", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PurchaseCreate(PurchaseFields):
    pass


class PurchaseUpdate(BaseModel):
    game_id: int | None = Field(default=None, gt=0)
    kind: PurchaseKind | None = None
    amount_minor: int | None = Field(default=None, ge=0, le=2_147_483_647)
    currency_code: str | None = Field(
        default=None, min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"
    )
    purchased_on: date | None = None
    platform: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("currency_code")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        return value.upper() if value is not None else None

    @field_validator("kind", "amount_minor")
    @classmethod
    def reject_required_nulls(cls, value: object | None) -> object:
        if value is None:
            raise ValueError("Field cannot be null when provided.")
        return value

    @field_validator("currency_code")
    @classmethod
    def reject_currency_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Currency cannot be null when provided.")
        return value

    @field_validator("platform", "notes")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class PurchaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int | None
    game_title: str | None
    kind: PurchaseKind
    amount_minor: int
    currency_code: str
    purchased_on: date | None
    platform: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class PurchaseListResponse(BaseModel):
    items: list[PurchaseResponse]
    total: int
    page: int
    page_size: int


class CurrencySpending(BaseModel):
    currency_code: str
    amount_minor: int
    purchase_count: int
    attributed_amount_minor: int
    played_seconds: int
    cost_per_hour_minor: int | None


class SpendingSummaryResponse(BaseModel):
    currencies: list[CurrencySpending]
    unassigned_purchase_count: int


class GameSpendingResponse(BaseModel):
    game_id: int
    game_title: str
    played_seconds: int
    purchase_count: int
    currencies: list[CurrencySpending]


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC)

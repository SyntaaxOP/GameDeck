"""Local purchase ledger model."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from gamedeck.db import Base


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('base_game', 'dlc', 'subscription', 'other')",
            name="ck_purchases_kind",
        ),
        CheckConstraint("amount_minor >= 0", name="ck_purchases_amount_nonnegative"),
        CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_purchases_currency_code",
        ),
        Index("ix_purchases_game_purchased", "game_id", "purchased_on"),
        Index("ix_purchases_purchased_on", "purchased_on"),
        Index("ix_purchases_currency_code", "currency_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int | None] = mapped_column(
        ForeignKey("games.id", ondelete="RESTRICT"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    purchased_on: Mapped[date | None] = mapped_column(Date)
    platform: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    game: Mapped["Game | None"] = relationship(back_populates="purchases")  # noqa: F821

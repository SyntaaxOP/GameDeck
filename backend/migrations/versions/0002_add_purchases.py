"""Add the Phase 9 local purchase ledger.

Revision ID: 0002
Revises: 0001
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "purchases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "game_id",
            sa.Integer(),
            sa.ForeignKey("games.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("purchased_on", sa.Date(), nullable=True),
        sa.Column("platform", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "kind IN ('base_game', 'dlc', 'subscription', 'other')",
            name="ck_purchases_kind",
        ),
        sa.CheckConstraint("amount_minor >= 0", name="ck_purchases_amount_nonnegative"),
        sa.CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_purchases_currency_code",
        ),
    )
    op.create_index("ix_purchases_game_purchased", "purchases", ["game_id", "purchased_on"])
    op.create_index("ix_purchases_purchased_on", "purchases", ["purchased_on"])
    op.create_index("ix_purchases_currency_code", "purchases", ["currency_code"])


def downgrade() -> None:
    op.drop_index("ix_purchases_currency_code", table_name="purchases")
    op.drop_index("ix_purchases_purchased_on", table_name="purchases")
    op.drop_index("ix_purchases_game_purchased", table_name="purchases")
    op.drop_table("purchases")

"""Add manual FiveM server companion records.

Revision ID: 0004
Revises: 0003
"""

from typing import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fivem_servers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("connect_code", sa.String(100), nullable=True),
        sa.Column("discord_url", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("favorite", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_joined_at", sa.DateTime(), nullable=True),
        sa.Column("tracked_playtime_seconds", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("tracked_playtime_seconds >= 0", name="ck_fivem_servers_playtime_nonnegative"),
    )
    op.execute("CREATE UNIQUE INDEX uq_fivem_servers_address_ci ON fivem_servers (lower(address))")
    op.create_index("ix_fivem_servers_favorite_last_joined", "fivem_servers", ["favorite", "last_joined_at"])


def downgrade() -> None:
    op.drop_index("ix_fivem_servers_favorite_last_joined", table_name="fivem_servers")
    op.execute("DROP INDEX uq_fivem_servers_address_ci")
    op.drop_table("fivem_servers")

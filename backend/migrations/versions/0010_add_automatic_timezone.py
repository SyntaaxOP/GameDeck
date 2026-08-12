"""Remember whether GameDeck follows the Windows/browser timezone.

Revision ID: 0010
Revises: 0009
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("settings") as batch:
        batch.add_column(sa.Column("time_zone_auto", sa.Boolean(), nullable=False, server_default=sa.text("1")))


def downgrade() -> None:
    with op.batch_alter_table("settings") as batch:
        batch.drop_column("time_zone_auto")

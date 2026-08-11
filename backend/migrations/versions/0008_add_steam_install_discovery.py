"""Add local Steam installation discovery metadata.

Revision ID: 0008
Revises: 0007
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("games") as batch:
        batch.add_column(sa.Column("install_directory", sa.Text(), nullable=True))
        batch.add_column(sa.Column("discovered_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("games") as batch:
        batch.drop_column("discovered_at")
        batch.drop_column("install_directory")

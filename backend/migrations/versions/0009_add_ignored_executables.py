"""Add durable ignored executable decisions.

Revision ID: 0009
Revises: 0008
"""
from typing import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        "ignored_executables",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("executable_name", sa.String(255), nullable=False),
        sa.Column("executable_path", sa.Text()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("executable_path", name="uq_ignored_executables_path"),
    )

def downgrade() -> None:
    op.drop_table("ignored_executables")

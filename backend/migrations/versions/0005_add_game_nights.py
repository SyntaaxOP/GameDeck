"""Add local game nights and attendees.

Revision ID: 0005
Revises: 0004
"""
from typing import Sequence
from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("game_nights",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("title", sa.String(200), nullable=False),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False), sa.Column("duration_minutes", sa.Integer(), server_default="120", nullable=False),
        sa.Column("status", sa.String(20), server_default="planned", nullable=False), sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('planned', 'completed', 'cancelled')", name="ck_game_nights_status"),
        sa.CheckConstraint("duration_minutes BETWEEN 30 AND 720", name="ck_game_nights_duration"))
    op.create_index("ix_game_nights_scheduled_status", "game_nights", ["scheduled_at", "status"])
    op.create_table("game_night_attendees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("game_night_id", sa.Integer(), sa.ForeignKey("game_nights.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False), sa.Column("response", sa.String(20), nullable=False),
        sa.CheckConstraint("response IN ('confirmed', 'maybe', 'declined')", name="ck_game_night_attendees_response"))
    op.execute("CREATE UNIQUE INDEX uq_game_night_attendees_name_ci ON game_night_attendees (game_night_id, lower(name))")


def downgrade() -> None:
    op.execute("DROP INDEX uq_game_night_attendees_name_ci")
    op.drop_table("game_night_attendees")
    op.drop_index("ix_game_nights_scheduled_status", table_name="game_nights")
    op.drop_table("game_nights")

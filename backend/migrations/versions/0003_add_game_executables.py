"""Add normalized executable mappings and aliases.

Revision ID: 0003
Revises: 0002
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "game_executables",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("game_id", sa.Integer(), sa.ForeignKey("games.id", ondelete="CASCADE"), nullable=False),
        sa.Column("executable_name", sa.String(length=255), nullable=False),
        sa.Column("executable_path", sa.Text(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_game_executables_game", "game_executables", ["game_id"])
    op.create_index(
        "uq_game_executables_primary_game", "game_executables", ["game_id"], unique=True,
        sqlite_where=sa.text("is_primary = 1"),
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_game_executables_active_name_ci "
        "ON game_executables (lower(executable_name)) WHERE active = 1"
    )
    op.execute(
        "INSERT INTO game_executables "
        "(game_id, executable_name, executable_path, is_primary, active, created_at, updated_at) "
        "SELECT id, executable_name, executable_path, 1, "
        "CASE WHEN archived_at IS NULL THEN 1 ELSE 0 END, created_at, updated_at FROM games"
    )
    op.execute("DROP INDEX uq_games_active_executable_name_ci")


def downgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX uq_games_active_executable_name_ci "
        "ON games (lower(executable_name)) WHERE archived_at IS NULL"
    )
    op.execute("DROP INDEX uq_game_executables_active_name_ci")
    op.drop_index("uq_game_executables_primary_game", table_name="game_executables")
    op.drop_index("ix_game_executables_game", table_name="game_executables")
    op.drop_table("game_executables")

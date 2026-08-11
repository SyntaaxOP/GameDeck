"""Create the Phase 1 GameDeck schema.

Revision ID: 0001
Revises: None
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "games",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("executable_name", sa.String(length=255), nullable=False),
        sa.Column("executable_path", sa.Text(), nullable=True),
        sa.Column("cover_path", sa.Text(), nullable=True),
        sa.Column("genre", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="backlog", nullable=False),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("personal_rating", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("favorite", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("date_added", sa.DateTime(), nullable=False),
        sa.Column("date_completed", sa.Date(), nullable=True),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "platform IN ('steam', 'xbox', 'epic', 'fivem', 'local', 'emulator', 'other')",
            name="ck_games_platform",
        ),
        sa.CheckConstraint(
            "status IN ('currently_playing', 'backlog', 'completed', "
            "'completed_100', 'dropped', 'paused')",
            name="ck_games_status",
        ),
        sa.CheckConstraint("priority IS NULL OR priority BETWEEN 1 AND 5", name="ck_games_priority"),
        sa.CheckConstraint(
            "personal_rating IS NULL OR personal_rating BETWEEN 1 AND 10",
            name="ck_games_personal_rating",
        ),
    )
    op.create_index("ix_games_status_archived", "games", ["status", "archived_at"])
    op.create_index("ix_games_favorite_archived", "games", ["favorite", "archived_at"])
    op.execute(
        "CREATE UNIQUE INDEX uq_games_active_executable_name_ci "
        "ON games (lower(executable_name)) WHERE archived_at IS NULL"
    )

    op.create_table(
        "game_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "game_id",
            sa.Integer(),
            sa.ForeignKey("games.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("detection_method", sa.String(length=20), nullable=False),
        sa.Column("end_reason", sa.String(length=30), nullable=True),
        sa.Column("process_id", sa.Integer(), nullable=True),
        sa.Column("process_started_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_game_sessions_end_after_start",
        ),
        sa.CheckConstraint(
            "last_seen_at >= started_at",
            name="ck_game_sessions_last_seen_after_start",
        ),
        sa.CheckConstraint(
            "(ended_at IS NULL AND duration_seconds IS NULL) OR "
            "(ended_at IS NOT NULL AND duration_seconds IS NOT NULL)",
            name="ck_game_sessions_completion_state",
        ),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_game_sessions_duration_nonnegative",
        ),
        sa.CheckConstraint(
            "detection_method IN ('process', 'manual', 'recovered')",
            name="ck_game_sessions_detection_method",
        ),
        sa.CheckConstraint(
            "end_reason IS NULL OR end_reason IN "
            "('process_stopped', 'tracker_shutdown', 'recovered', 'manual')",
            name="ck_game_sessions_end_reason",
        ),
    )
    op.create_index(
        "ix_game_sessions_game_started", "game_sessions", ["game_id", "started_at"]
    )
    op.create_index(
        "ix_game_sessions_started_ended", "game_sessions", ["started_at", "ended_at"]
    )
    op.create_index("ix_game_sessions_ended_at", "game_sessions", ["ended_at"])
    op.create_index(
        "uq_game_sessions_active_game",
        "game_sessions",
        ["game_id"],
        unique=True,
        sqlite_where=sa.text("ended_at IS NULL"),
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scan_interval_seconds", sa.Integer(), server_default="5", nullable=False),
        sa.Column("restart_grace_seconds", sa.Integer(), server_default="15", nullable=False),
        sa.Column("tracking_enabled", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column("week_starts_on", sa.Integer(), server_default="0", nullable=False),
        sa.Column("time_zone", sa.String(length=100), server_default="UTC", nullable=False),
        sa.Column("theme", sa.String(length=10), server_default="dark", nullable=False),
        sa.Column("currency_code", sa.String(length=3), server_default="PHP", nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_settings_singleton"),
        sa.CheckConstraint(
            "scan_interval_seconds BETWEEN 2 AND 60",
            name="ck_settings_scan_interval",
        ),
        sa.CheckConstraint(
            "restart_grace_seconds BETWEEN 0 AND 120",
            name="ck_settings_restart_grace",
        ),
        sa.CheckConstraint("week_starts_on BETWEEN 0 AND 6", name="ck_settings_week_start"),
        sa.CheckConstraint("theme IN ('dark', 'light', 'system')", name="ck_settings_theme"),
        sa.CheckConstraint(
            "length(currency_code) = 3 AND currency_code = upper(currency_code)",
            name="ck_settings_currency_code",
        ),
    )
    op.execute("INSERT INTO settings (id, updated_at) VALUES (1, CURRENT_TIMESTAMP)")


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_index("uq_game_sessions_active_game", table_name="game_sessions")
    op.drop_index("ix_game_sessions_ended_at", table_name="game_sessions")
    op.drop_index("ix_game_sessions_started_ended", table_name="game_sessions")
    op.drop_index("ix_game_sessions_game_started", table_name="game_sessions")
    op.drop_table("game_sessions")
    op.execute("DROP INDEX uq_games_active_executable_name_ci")
    op.drop_index("ix_games_favorite_archived", table_name="games")
    op.drop_index("ix_games_status_archived", table_name="games")
    op.drop_table("games")

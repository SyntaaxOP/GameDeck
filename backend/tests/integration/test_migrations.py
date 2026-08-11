import sqlite3


def test_initial_migration_creates_expected_schema(migrated_database: tuple[object, str]) -> None:
    database_path, _ = migrated_database

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        settings = connection.execute(
            "SELECT id, scan_interval_seconds, restart_grace_seconds, "
            "tracking_enabled, week_starts_on, time_zone, theme, currency_code FROM settings"
        ).fetchone()
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }
        game_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(games)").fetchall()
        }

    assert {"alembic_version", "games", "game_executables", "game_sessions", "settings"} <= tables
    assert settings == (1, 5, 15, 1, 0, "UTC", "dark", "PHP")
    assert "uq_game_executables_active_name_ci" in indexes
    assert "uq_game_executables_primary_game" in indexes
    assert "uq_game_sessions_active_game" in indexes
    assert {"steam_app_id", "install_directory", "discovered_at"} <= game_columns
    assert "ignored_executables" in tables

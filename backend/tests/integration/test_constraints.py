from datetime import UTC, datetime, timedelta
import sqlite3

import pytest


NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC).replace(tzinfo=None).isoformat(sep=" ")


def insert_game(connection: sqlite3.Connection, executable_name: str = "sample.exe") -> int:
    cursor = connection.execute(
        """
        INSERT INTO games (
            title, platform, executable_name, status, favorite,
            date_added, created_at, updated_at
        ) VALUES (?, 'local', ?, 'backlog', 0, ?, ?, ?)
        """,
        ("Sample Game", executable_name, NOW, NOW, NOW),
    )
    return int(cursor.lastrowid)


def insert_active_session(connection: sqlite3.Connection, game_id: int) -> None:
    connection.execute(
        """
        INSERT INTO game_sessions (
            game_id, started_at, last_seen_at, detection_method, created_at, updated_at
        ) VALUES (?, ?, ?, 'process', ?, ?)
        """,
        (game_id, NOW, NOW, NOW, NOW),
    )


def insert_executable_mapping(
    connection: sqlite3.Connection, game_id: int, executable_name: str, *, active: bool = True
) -> None:
    connection.execute(
        """
        INSERT INTO game_executables (
            game_id, executable_name, is_primary, active, created_at, updated_at
        ) VALUES (?, ?, 1, ?, ?, ?)
        """,
        (game_id, executable_name, active, NOW, NOW),
    )


def test_only_one_active_session_is_allowed_per_game(
    migrated_database: tuple[object, str],
) -> None:
    database_path, _ = migrated_database
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        game_id = insert_game(connection)
        insert_active_session(connection, game_id)

        with pytest.raises(sqlite3.IntegrityError):
            insert_active_session(connection, game_id)


def test_ended_session_cannot_end_before_it_started(
    migrated_database: tuple[object, str],
) -> None:
    database_path, _ = migrated_database
    with sqlite3.connect(database_path) as connection:
        game_id = insert_game(connection)
        before_start = (
            datetime.fromisoformat(NOW) - timedelta(seconds=1)
        ).isoformat(sep=" ")

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO game_sessions (
                    game_id, started_at, ended_at, last_seen_at, duration_seconds,
                    detection_method, end_reason, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 0, 'manual', 'manual', ?, ?)
                """,
                (game_id, NOW, before_start, NOW, NOW, NOW),
            )


def test_active_and_completed_fields_must_be_consistent(
    migrated_database: tuple[object, str],
) -> None:
    database_path, _ = migrated_database
    with sqlite3.connect(database_path) as connection:
        game_id = insert_game(connection)

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO game_sessions (
                    game_id, started_at, last_seen_at, duration_seconds,
                    detection_method, created_at, updated_at
                ) VALUES (?, ?, ?, 10, 'process', ?, ?)
                """,
                (game_id, NOW, NOW, NOW, NOW),
            )


def test_session_requires_an_existing_game(migrated_database: tuple[object, str]) -> None:
    database_path, _ = migrated_database
    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys=ON")

        with pytest.raises(sqlite3.IntegrityError):
            insert_active_session(connection, 999)


def test_active_executable_names_are_case_insensitively_unique(
    migrated_database: tuple[object, str],
) -> None:
    database_path, _ = migrated_database
    with sqlite3.connect(database_path) as connection:
        first_id = insert_game(connection, "Game.exe")
        second_id = insert_game(connection, "game.EXE")
        insert_executable_mapping(connection, first_id, "Game.exe")

        with pytest.raises(sqlite3.IntegrityError):
            insert_executable_mapping(connection, second_id, "game.EXE")


def test_settings_table_allows_only_singleton_row(migrated_database: tuple[object, str]) -> None:
    database_path, _ = migrated_database
    with sqlite3.connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO settings (id, updated_at) VALUES (2, ?)",
                (NOW,),
            )

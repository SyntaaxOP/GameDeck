"""Create a deterministic, non-destructive portfolio demo library."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Sequence

from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gamedeck.config import AppSettings, BACKEND_DIR, get_settings
from gamedeck.db import Database
from gamedeck.models.game import Game
from gamedeck.models.game_executable import GameExecutable
from gamedeck.models.game_session import GameSession
from gamedeck.models.purchase import Purchase


@dataclass(frozen=True)
class DemoGame:
    title: str
    platform: str
    status: str
    genre: str
    priority: int | None = None
    rating: int | None = None
    favorite: bool = False
    aliases: tuple[str, ...] = ()

    @property
    def executable_name(self) -> str:
        slug = "-".join(self.title.lower().replace(":", "").split())
        return f"gamedeck-demo-{slug}.exe"


DEMO_GAMES: tuple[DemoGame, ...] = (
    DemoGame("Hades II", "steam", "currently_playing", "Action roguelike", 1, 9, True, ("gamedeck-demo-hades-ii-shipping.exe",)),
    DemoGame("Cyberpunk 2077", "steam", "currently_playing", "Action RPG", 2, 9, True, ("gamedeck-demo-cyberpunk-launcher.exe",)),
    DemoGame("Balatro", "steam", "backlog", "Deckbuilder", 1, None, True),
    DemoGame("Forza Horizon 5", "xbox", "paused", "Racing", 3, 8),
    DemoGame("Outer Wilds", "epic", "completed", "Adventure", None, 10, True),
    DemoGame("Celeste", "steam", "completed_100", "Platformer", None, 10, True),
    DemoGame("Disco Elysium", "local", "backlog", "Narrative RPG", 2),
    DemoGame("Tunic", "xbox", "backlog", "Action adventure", 4),
)

# (game index, days before anchor, start hour UTC, duration minutes)
DEMO_SESSIONS: tuple[tuple[int, int, int, int], ...] = (
    (0, 1, 19, 105), (1, 2, 20, 80), (0, 3, 18, 95), (3, 4, 21, 55),
    (1, 5, 19, 125), (0, 7, 20, 70), (4, 8, 18, 150), (3, 10, 21, 45),
    (1, 12, 19, 110), (0, 14, 18, 85), (5, 16, 20, 130), (4, 18, 19, 90),
    (1, 21, 20, 75), (5, 24, 18, 100), (4, 27, 19, 115), (3, 30, 20, 65),
)

# (game index or None, kind, amount minor, currency, days before anchor, store)
DEMO_PURCHASES: tuple[tuple[int | None, str, int, str, int, str], ...] = (
    (0, "base_game", 109_900, "PHP", 58, "Steam"),
    (1, "base_game", 299_900, "PHP", 120, "Steam"),
    (2, "base_game", 89_900, "PHP", 35, "Steam"),
    (3, "base_game", 249_900, "PHP", 180, "Xbox"),
    (4, "base_game", 79_900, "PHP", 240, "Epic Games"),
    (5, "base_game", 59_900, "PHP", 300, "Steam"),
    (7, "base_game", 2_999, "USD", 90, "Xbox"),
    (None, "subscription", 49_900, "PHP", 12, "PC Game Pass"),
)


def parse_anchor(value: str) -> datetime:
    """Parse an ISO timestamp and normalize it to naive UTC storage."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("--at must include a UTC offset, for example 2026-08-11T12:00:00Z")
    return parsed.astimezone(UTC).replace(tzinfo=None, minute=0, second=0, microsecond=0)


def seed_demo_data(session: Session, anchor: datetime) -> tuple[int, int, int]:
    """Insert missing demo records while preserving every existing record."""
    created_games = 0
    games_by_index: dict[int, Game] = {}
    new_game_indices: set[int] = set()

    for index, spec in enumerate(DEMO_GAMES):
        game = session.scalar(
            select(Game).where(func.lower(Game.executable_name) == spec.executable_name.lower())
        )
        if game is None:
            added_at = anchor - timedelta(days=60 - index * 4)
            completed_at = (anchor - timedelta(days=25 - index)).date() if spec.status.startswith("completed") else None
            game = Game(
                title=spec.title,
                platform=spec.platform,
                executable_name=spec.executable_name,
                executable_path=None,
                cover_path=None,
                genre=spec.genre,
                status=spec.status,
                priority=spec.priority,
                personal_rating=spec.rating,
                notes="Portfolio demo record — safe to archive after exploring GameDeck.",
                favorite=spec.favorite,
                date_added=added_at,
                date_completed=completed_at,
                archived_at=None,
                created_at=added_at,
                updated_at=added_at,
            )
            session.add(game)
            session.flush()
            session.add(GameExecutable(
                game_id=game.id,
                executable_name=game.executable_name,
                executable_path=None,
                is_primary=True,
                active=True,
                created_at=added_at,
                updated_at=added_at,
            ))
            for alias in spec.aliases:
                session.add(GameExecutable(
                    game_id=game.id,
                    executable_name=alias,
                    executable_path=None,
                    is_primary=False,
                    active=True,
                    created_at=added_at,
                    updated_at=added_at,
                ))
            created_games += 1
            new_game_indices.add(index)
        games_by_index[index] = game

    created_sessions = 0
    for game_index, days_ago, hour, minutes in DEMO_SESSIONS:
        if game_index not in new_game_indices:
            continue
        game = games_by_index[game_index]
        started_at = (anchor - timedelta(days=days_ago)).replace(hour=hour)
        ended_at = started_at + timedelta(minutes=minutes)
        exists = session.scalar(
            select(GameSession.id).where(
                GameSession.game_id == game.id,
                GameSession.started_at == started_at,
                GameSession.ended_at == ended_at,
            )
        )
        if exists is not None:
            continue
        game_session = GameSession(
            game_id=game.id,
            started_at=started_at,
            ended_at=ended_at,
            last_seen_at=ended_at,
            duration_seconds=minutes * 60,
            detection_method="manual",
            end_reason="manual",
            process_id=None,
            process_started_at=None,
            created_at=ended_at,
            updated_at=ended_at,
        )
        session.add(game_session)
        created_sessions += 1

    created_purchases = 0
    if new_game_indices:
        for game_index, kind, amount_minor, currency, days_ago, platform in DEMO_PURCHASES:
            game = games_by_index[game_index] if game_index is not None else None
            session.add(Purchase(
                game_id=game.id if game is not None else None,
                kind=kind,
                amount_minor=amount_minor,
                currency_code=currency,
                purchased_on=(anchor - timedelta(days=days_ago)).date(),
                platform=platform,
                notes="Portfolio demo purchase — no real financial data.",
                created_at=anchor,
                updated_at=anchor,
            ))
            created_purchases += 1

    session.commit()
    return created_games, created_sessions, created_purchases


def migrate(database_url: str) -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = database_url
    command.upgrade(config, "head")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=get_settings().database_url)
    parser.add_argument(
        "--at",
        type=parse_anchor,
        default=datetime.now(UTC).replace(tzinfo=None, minute=0, second=0, microsecond=0),
        help="Anchor timestamp with UTC offset (default: current UTC hour)",
    )
    parser.add_argument("--skip-migrations", action="store_true", help="Do not run Alembic first")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.skip_migrations:
        migrate(args.database_url)
    settings = AppSettings(database_url=args.database_url)
    database = Database(settings)
    try:
        with database.session_factory() as session:
            games, sessions, purchases = seed_demo_data(session, args.at)
    finally:
        database.dispose()
    location = args.database_url.removeprefix("sqlite:///")
    if location != args.database_url:
        location = str(Path(location).resolve())
    print(
        f"Demo ready: {games} games, {sessions} sessions, and "
        f"{purchases} purchases added to {location}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gamedeck.demo import DEMO_GAMES, DEMO_PURCHASES, DEMO_SESSIONS, seed_demo_data
from gamedeck.models.game import Game
from gamedeck.models.game_executable import GameExecutable
from gamedeck.models.game_session import GameSession
from gamedeck.models.purchase import Purchase


def test_demo_seed_is_repeatable_and_non_destructive(db_session: Session) -> None:
    existing = Game(
        title="My real game",
        platform="local",
        executable_name="my-real-game.exe",
        status="backlog",
        favorite=False,
        date_added=datetime(2026, 1, 1),
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    db_session.add(existing)
    db_session.commit()

    anchor = datetime(2026, 8, 11, 12)
    assert seed_demo_data(db_session, anchor) == (
        len(DEMO_GAMES), len(DEMO_SESSIONS), len(DEMO_PURCHASES)
    )
    assert seed_demo_data(db_session, datetime(2026, 9, 15, 8)) == (0, 0, 0)

    assert db_session.scalar(select(func.count()).select_from(Game)) == len(DEMO_GAMES) + 1
    assert db_session.scalar(select(func.count()).select_from(GameSession)) == len(DEMO_SESSIONS)
    assert db_session.scalar(select(func.count()).select_from(Purchase)) == len(DEMO_PURCHASES)
    assert db_session.scalar(select(func.count()).select_from(GameExecutable)) == len(DEMO_GAMES) + 2
    assert db_session.scalar(select(Game).where(Game.executable_name == "my-real-game.exe")) is not None


def test_demo_seed_uses_the_requested_anchor(db_session: Session) -> None:
    seed_demo_data(db_session, datetime(2026, 8, 11, 12))
    latest = db_session.scalar(select(GameSession).order_by(GameSession.started_at.desc()))
    assert latest is not None
    assert latest.started_at == datetime(2026, 8, 10, 19)

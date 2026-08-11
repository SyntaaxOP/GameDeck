"""Session reads used by analytics."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from gamedeck.models.game_session import GameSession


class AnalyticsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def all_sessions(self) -> list[GameSession]:
        statement = (
            select(GameSession)
            .options(joinedload(GameSession.game))
            .order_by(GameSession.started_at.desc(), GameSession.id.desc())
        )
        return list(self.session.scalars(statement))

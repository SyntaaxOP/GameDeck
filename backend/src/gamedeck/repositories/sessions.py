"""Database access for game sessions."""

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from gamedeck.models.game_session import GameSession


class SessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, game_session: GameSession) -> GameSession:
        self.session.add(game_session)
        self.session.flush()
        return game_session

    def get(self, session_id: int) -> GameSession | None:
        statement = (
            select(GameSession)
            .options(joinedload(GameSession.game))
            .where(GameSession.id == session_id)
        )
        return self.session.scalar(statement)

    def get_active(self, game_id: int) -> GameSession | None:
        statement = (
            select(GameSession)
            .options(joinedload(GameSession.game))
            .where(GameSession.game_id == game_id, GameSession.ended_at.is_(None))
        )
        return self.session.scalar(statement)

    def list_active(self) -> list[GameSession]:
        statement = (
            select(GameSession)
            .options(joinedload(GameSession.game))
            .where(GameSession.ended_at.is_(None))
            .order_by(GameSession.started_at.asc(), GameSession.id.asc())
        )
        return list(self.session.scalars(statement))

    def overlaps(
        self,
        *,
        game_id: int,
        started_at: datetime,
        ended_at: datetime,
        exclude_session_id: int | None = None,
    ) -> bool:
        filters = [
            GameSession.game_id == game_id,
            GameSession.started_at < ended_at,
            or_(GameSession.ended_at.is_(None), GameSession.ended_at > started_at),
        ]
        if exclude_session_id is not None:
            filters.append(GameSession.id != exclude_session_id)
        statement = select(GameSession.id).where(*filters).limit(1)
        return self.session.scalar(statement) is not None

    def list(
        self,
        *,
        game_id: int | None,
        from_at: datetime | None,
        to_at: datetime | None,
        active: bool | None,
        page: int,
        page_size: int,
    ) -> tuple[list[GameSession], int]:
        filters = []
        if game_id is not None:
            filters.append(GameSession.game_id == game_id)
        if from_at is not None:
            filters.append(or_(GameSession.ended_at.is_(None), GameSession.ended_at > from_at))
        if to_at is not None:
            filters.append(GameSession.started_at < to_at)
        if active is not None:
            filters.append(GameSession.ended_at.is_(None) if active else GameSession.ended_at.is_not(None))

        statement = (
            select(GameSession)
            .options(joinedload(GameSession.game))
            .where(*filters)
            .order_by(GameSession.started_at.desc(), GameSession.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count()).select_from(GameSession).where(*filters)
        return list(self.session.scalars(statement)), int(self.session.scalar(count_statement) or 0)

    def delete(self, game_session: GameSession) -> None:
        self.session.delete(game_session)


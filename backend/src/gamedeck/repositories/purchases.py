"""Database access for purchases and cost-per-hour inputs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from gamedeck.models.game_session import GameSession
from gamedeck.models.purchase import Purchase


class PurchaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, purchase: Purchase) -> Purchase:
        self.session.add(purchase)
        self.session.flush()
        return purchase

    def get(self, purchase_id: int) -> Purchase | None:
        statement = (
            select(Purchase)
            .options(joinedload(Purchase.game))
            .where(Purchase.id == purchase_id)
        )
        return self.session.scalar(statement)

    def list(
        self, *, game_id: int | None, unassigned: bool, page: int, page_size: int
    ) -> tuple[list[Purchase], int]:
        filters = []
        if game_id is not None:
            filters.append(Purchase.game_id == game_id)
        elif unassigned:
            filters.append(Purchase.game_id.is_(None))
        statement = (
            select(Purchase)
            .options(joinedload(Purchase.game))
            .where(*filters)
            .order_by(Purchase.purchased_on.desc().nulls_last(), Purchase.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = select(func.count()).select_from(Purchase).where(*filters)
        return list(self.session.scalars(statement)), int(self.session.scalar(count_statement) or 0)

    def all(self, *, game_id: int | None = None) -> list[Purchase]:
        statement = select(Purchase).options(joinedload(Purchase.game))
        if game_id is not None:
            statement = statement.where(Purchase.game_id == game_id)
        return list(self.session.scalars(statement.order_by(Purchase.id.asc())))

    def completed_playtime_by_game(self) -> dict[int, int]:
        statement = (
            select(GameSession.game_id, func.coalesce(func.sum(GameSession.duration_seconds), 0))
            .where(GameSession.ended_at.is_not(None))
            .group_by(GameSession.game_id)
        )
        return {int(game_id): int(seconds) for game_id, seconds in self.session.execute(statement)}

    def delete(self, purchase: Purchase) -> None:
        self.session.delete(purchase)

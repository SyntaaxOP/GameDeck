"""Purchase ledger rules and local spending analytics."""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from gamedeck.domain.errors import GameNotFoundError, PurchaseNotFoundError
from gamedeck.models.game import Game
from gamedeck.models.purchase import Purchase
from gamedeck.repositories.purchases import PurchaseRepository
from gamedeck.schemas.purchase import (
    CurrencySpending,
    GameSpendingResponse,
    PurchaseCreate,
    PurchaseListResponse,
    PurchaseResponse,
    PurchaseUpdate,
    SpendingSummaryResponse,
    as_utc,
)
from gamedeck.services.games import utc_now


def cost_per_hour(amount_minor: int, played_seconds: int) -> int | None:
    if played_seconds <= 0:
        return None
    return (amount_minor * 3_600 + played_seconds // 2) // played_seconds


class PurchaseService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = PurchaseRepository(session)

    def create(self, payload: PurchaseCreate) -> PurchaseResponse:
        if payload.game_id is not None:
            self._get_game(payload.game_id)
        now = utc_now()
        purchase = Purchase(**payload.model_dump(mode="python"), created_at=now, updated_at=now)
        self.repository.add(purchase)
        self.session.commit()
        return self.to_response(self.get_model(purchase.id))

    def get_model(self, purchase_id: int) -> Purchase:
        purchase = self.repository.get(purchase_id)
        if purchase is None:
            raise PurchaseNotFoundError(f"Purchase {purchase_id} was not found.")
        return purchase

    def get(self, purchase_id: int) -> PurchaseResponse:
        return self.to_response(self.get_model(purchase_id))

    def list(
        self, *, game_id: int | None, unassigned: bool, page: int, page_size: int
    ) -> PurchaseListResponse:
        if game_id is not None:
            self._get_game(game_id)
        purchases, total = self.repository.list(
            game_id=game_id, unassigned=unassigned, page=page, page_size=page_size
        )
        return PurchaseListResponse(
            items=[self.to_response(item) for item in purchases],
            total=total,
            page=page,
            page_size=page_size,
        )

    def update(self, purchase_id: int, payload: PurchaseUpdate) -> PurchaseResponse:
        purchase = self.get_model(purchase_id)
        values = payload.model_dump(exclude_unset=True, mode="python")
        if "game_id" in values and values["game_id"] is not None:
            self._get_game(int(values["game_id"]))
        for field, value in values.items():
            if field in {"kind"} and value is not None:
                value = value.value
            setattr(purchase, field, value)
        if values:
            purchase.updated_at = utc_now()
            self.session.commit()
        return self.to_response(self.get_model(purchase_id))

    def delete(self, purchase_id: int) -> None:
        purchase = self.get_model(purchase_id)
        self.repository.delete(purchase)
        self.session.commit()

    def summary(self) -> SpendingSummaryResponse:
        purchases = self.repository.all()
        playtime = self.repository.completed_playtime_by_game()
        grouped: dict[str, list[Purchase]] = defaultdict(list)
        for purchase in purchases:
            grouped[purchase.currency_code].append(purchase)
        currencies = [
            self._currency_summary(code, items, playtime)
            for code, items in sorted(grouped.items())
        ]
        return SpendingSummaryResponse(
            currencies=currencies,
            unassigned_purchase_count=sum(item.game_id is None for item in purchases),
        )

    def game_summary(self, game_id: int) -> GameSpendingResponse:
        game = self._get_game(game_id)
        purchases = self.repository.all(game_id=game_id)
        playtime = self.repository.completed_playtime_by_game()
        grouped: dict[str, list[Purchase]] = defaultdict(list)
        for purchase in purchases:
            grouped[purchase.currency_code].append(purchase)
        currencies = [
            self._currency_summary(code, items, playtime)
            for code, items in sorted(grouped.items())
        ]
        return GameSpendingResponse(
            game_id=game.id,
            game_title=game.title,
            played_seconds=playtime.get(game.id, 0),
            purchase_count=len(purchases),
            currencies=currencies,
        )

    @staticmethod
    def _currency_summary(
        code: str, purchases: list[Purchase], playtime: dict[int, int]
    ) -> CurrencySpending:
        amount = sum(item.amount_minor for item in purchases)
        attributed = [item for item in purchases if item.game_id is not None]
        attributed_amount = sum(item.amount_minor for item in attributed)
        game_ids = {int(item.game_id) for item in attributed if item.game_id is not None}
        played_seconds = sum(playtime.get(game_id, 0) for game_id in game_ids)
        return CurrencySpending(
            currency_code=code,
            amount_minor=amount,
            purchase_count=len(purchases),
            attributed_amount_minor=attributed_amount,
            played_seconds=played_seconds,
            cost_per_hour_minor=cost_per_hour(attributed_amount, played_seconds),
        )

    def _get_game(self, game_id: int) -> Game:
        game = self.session.get(Game, game_id)
        if game is None:
            raise GameNotFoundError(f"Game {game_id} was not found.")
        return game

    @staticmethod
    def to_response(purchase: Purchase) -> PurchaseResponse:
        return PurchaseResponse(
            id=purchase.id,
            game_id=purchase.game_id,
            game_title=purchase.game.title if purchase.game is not None else None,
            kind=purchase.kind,
            amount_minor=purchase.amount_minor,
            currency_code=purchase.currency_code,
            purchased_on=purchase.purchased_on,
            platform=purchase.platform,
            notes=purchase.notes,
            created_at=as_utc(purchase.created_at),
            updated_at=as_utc(purchase.updated_at),
        )

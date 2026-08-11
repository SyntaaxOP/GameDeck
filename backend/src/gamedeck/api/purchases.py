"""Purchase ledger and spending analytics HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.purchase import (
    GameSpendingResponse,
    PurchaseCreate,
    PurchaseListResponse,
    PurchaseResponse,
    PurchaseUpdate,
    SpendingSummaryResponse,
)
from gamedeck.services.purchases import PurchaseService


router = APIRouter(tags=["spending"])
DatabaseSession = Annotated[Session, Depends(get_db_session)]


@router.get("/api/v1/purchases", response_model=PurchaseListResponse)
def list_purchases(
    session: DatabaseSession,
    game_id: Annotated[int | None, Query(gt=0)] = None,
    unassigned: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PurchaseListResponse:
    return PurchaseService(session).list(
        game_id=game_id, unassigned=unassigned, page=page, page_size=page_size
    )


@router.post(
    "/api/v1/purchases", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED
)
def create_purchase(payload: PurchaseCreate, session: DatabaseSession) -> PurchaseResponse:
    return PurchaseService(session).create(payload)


@router.get("/api/v1/purchases/{purchase_id}", response_model=PurchaseResponse)
def get_purchase(purchase_id: int, session: DatabaseSession) -> PurchaseResponse:
    return PurchaseService(session).get(purchase_id)


@router.patch("/api/v1/purchases/{purchase_id}", response_model=PurchaseResponse)
def update_purchase(
    purchase_id: int, payload: PurchaseUpdate, session: DatabaseSession
) -> PurchaseResponse:
    return PurchaseService(session).update(purchase_id, payload)


@router.delete("/api/v1/purchases/{purchase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_purchase(purchase_id: int, session: DatabaseSession) -> Response:
    PurchaseService(session).delete(purchase_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api/v1/spending/summary", response_model=SpendingSummaryResponse)
def spending_summary(session: DatabaseSession) -> SpendingSummaryResponse:
    return PurchaseService(session).summary()


@router.get("/api/v1/spending/games/{game_id}", response_model=GameSpendingResponse)
def game_spending(game_id: int, session: DatabaseSession) -> GameSpendingResponse:
    return PurchaseService(session).game_summary(game_id)

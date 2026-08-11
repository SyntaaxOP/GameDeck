"""Analytics HTTP routes."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.analytics import (
    DashboardResponse,
    DistributionDimension,
    DistributionResponse,
    GameAnalyticsResponse,
    PlaytimeResponse,
    TimeBucket,
)
from gamedeck.services.analytics import AnalyticsService


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
DatabaseSession = Annotated[Session, Depends(get_db_session)]


def now_utc() -> datetime:
    return datetime.now(UTC)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(
    session: DatabaseSession,
    at: datetime | None = None,
) -> DashboardResponse:
    return AnalyticsService(session).dashboard(at or now_utc())


@router.get("/playtime", response_model=PlaytimeResponse)
def playtime(
    session: DatabaseSession,
    from_at: Annotated[datetime, Query(alias="from")],
    to_at: Annotated[datetime, Query(alias="to")],
    bucket: TimeBucket = TimeBucket.DAY,
    game_id: Annotated[int | None, Query(gt=0)] = None,
    at: datetime | None = None,
) -> PlaytimeResponse:
    return AnalyticsService(session).playtime(
        from_at=from_at,
        to_at=to_at,
        bucket=bucket,
        game_id=game_id,
        at=at or now_utc(),
    )


@router.get("/distribution", response_model=DistributionResponse)
def distribution(
    session: DatabaseSession,
    from_at: Annotated[datetime, Query(alias="from")],
    to_at: Annotated[datetime, Query(alias="to")],
    dimension: DistributionDimension,
    at: datetime | None = None,
) -> DistributionResponse:
    return AnalyticsService(session).distribution(
        from_at=from_at,
        to_at=to_at,
        dimension=dimension,
        at=at or now_utc(),
    )


@router.get("/games/{game_id}", response_model=GameAnalyticsResponse)
def game_analytics(
    game_id: int,
    session: DatabaseSession,
    from_at: Annotated[datetime, Query(alias="from")],
    to_at: Annotated[datetime, Query(alias="to")],
    at: datetime | None = None,
) -> GameAnalyticsResponse:
    return AnalyticsService(session).game(
        game_id,
        from_at=from_at,
        to_at=to_at,
        at=at or now_utc(),
    )

"""Analytics API response contracts."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from gamedeck.schemas.session import SessionResponse


class TimeBucket(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class DistributionDimension(StrEnum):
    WEEKDAY = "weekday"
    HOUR = "hour"


class AnalyticsSummary(BaseModel):
    total_seconds: int
    session_count: int
    average_session_seconds: int
    longest_session_seconds: int


class GamePlaytime(BaseModel):
    game_id: int
    game_title: str
    total_seconds: int
    session_count: int


class SeriesPoint(BaseModel):
    bucket_start: datetime
    label: str
    total_seconds: int


class DistributionPoint(BaseModel):
    key: int
    label: str
    total_seconds: int


class PlaytimeResponse(BaseModel):
    from_at: datetime
    to_at: datetime
    time_zone: str
    bucket: TimeBucket
    summary: AnalyticsSummary
    series: list[SeriesPoint]
    games: list[GamePlaytime]


class DistributionResponse(BaseModel):
    from_at: datetime
    to_at: datetime
    time_zone: str
    dimension: DistributionDimension
    buckets: list[DistributionPoint]


class DashboardResponse(BaseModel):
    at: datetime
    time_zone: str
    today_seconds: int
    week_seconds: int
    month_seconds: int
    lifetime: AnalyticsSummary
    top_game: GamePlaytime | None
    current_sessions: list[SessionResponse]
    recent_sessions: list[SessionResponse]
    daily_series: list[SeriesPoint]


class GameAnalyticsResponse(BaseModel):
    game_id: int
    game_title: str
    from_at: datetime
    to_at: datetime
    time_zone: str
    summary: AnalyticsSummary
    daily_series: list[SeriesPoint]

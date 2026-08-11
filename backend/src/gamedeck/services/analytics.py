"""Timezone-aware, interval-clipped playtime analytics."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from gamedeck.domain.errors import GameNotFoundError, InvalidSessionError
from gamedeck.models.game import Game
from gamedeck.models.game_session import GameSession
from gamedeck.repositories.analytics import AnalyticsRepository
from gamedeck.schemas.analytics import (
    AnalyticsSummary,
    DashboardResponse,
    DistributionDimension,
    DistributionPoint,
    DistributionResponse,
    GameAnalyticsResponse,
    GamePlaytime,
    PlaytimeResponse,
    SeriesPoint,
    TimeBucket,
)
from gamedeck.services.sessions import SessionService, as_utc
from gamedeck.services.settings import SettingsService


MAX_RANGE = timedelta(days=366)
WEEKDAY_LABELS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def _aware(value: datetime | None, *, default: datetime | None = None) -> datetime:
    result = value or default
    if result is None or result.tzinfo is None or result.utcoffset() is None:
        raise InvalidSessionError("Analytics timestamps must include a UTC offset or timezone.")
    return result.astimezone(UTC)


def _local_midnight(value: date, zone: ZoneInfo) -> datetime:
    return datetime.combine(value, time.min, tzinfo=zone)


def _next_month(value: date) -> date:
    return date(value.year + (value.month == 12), 1 if value.month == 12 else value.month + 1, 1)


def clipped_seconds(session: GameSession, start: datetime, end: datetime, at: datetime) -> int:
    session_start = as_utc(session.started_at)
    session_end = as_utc(session.ended_at) if session.ended_at is not None else at
    clipped_start = max(session_start, start)
    clipped_end = min(session_end, end, at)
    return max(0, int((clipped_end - clipped_start).total_seconds()))


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AnalyticsRepository(session)
        settings = SettingsService(session).get_model()
        self.zone = ZoneInfo(settings.time_zone)
        self.time_zone = settings.time_zone
        self.week_starts_on = settings.week_starts_on

    def dashboard(self, at: datetime) -> DashboardResponse:
        at_utc = _aware(at)
        local = at_utc.astimezone(self.zone)
        today = _local_midnight(local.date(), self.zone).astimezone(UTC)
        tomorrow = _local_midnight(local.date() + timedelta(days=1), self.zone).astimezone(UTC)
        week_date = local.date() - timedelta(days=(local.weekday() - self.week_starts_on) % 7)
        week = _local_midnight(week_date, self.zone).astimezone(UTC)
        month = _local_midnight(local.date().replace(day=1), self.zone).astimezone(UTC)
        sessions = self.repository.all_sessions()
        lifetime_start = min((as_utc(item.started_at) for item in sessions), default=at_utc)
        recent = [item for item in sessions if item.ended_at is not None][:5]
        active = [item for item in sessions if item.ended_at is None]
        daily_start = _local_midnight(local.date() - timedelta(days=6), self.zone).astimezone(UTC)
        month_games = self._games(sessions, month, at_utc, at_utc)
        return DashboardResponse(
            at=at_utc,
            time_zone=self.time_zone,
            today_seconds=self._total(sessions, today, min(tomorrow, at_utc), at_utc),
            week_seconds=self._total(sessions, week, at_utc, at_utc),
            month_seconds=self._total(sessions, month, at_utc, at_utc),
            lifetime=self._summary(sessions, lifetime_start, at_utc, at_utc),
            top_game=month_games[0] if month_games else None,
            current_sessions=[SessionService(self.session).to_response(item) for item in active],
            recent_sessions=[SessionService(self.session).to_response(item) for item in recent],
            daily_series=self._series(sessions, daily_start, at_utc, TimeBucket.DAY, at_utc),
        )

    def playtime(
        self,
        *,
        from_at: datetime,
        to_at: datetime,
        bucket: TimeBucket,
        game_id: int | None,
        at: datetime,
    ) -> PlaytimeResponse:
        start, end, now = self._range(from_at, to_at, at)
        sessions = self.repository.all_sessions()
        if game_id is not None:
            self._require_game(game_id)
            sessions = [item for item in sessions if item.game_id == game_id]
        return PlaytimeResponse(
            from_at=start,
            to_at=end,
            time_zone=self.time_zone,
            bucket=bucket,
            summary=self._summary(sessions, start, end, now),
            series=self._series(sessions, start, end, bucket, now),
            games=self._games(sessions, start, end, now),
        )

    def distribution(
        self,
        *,
        from_at: datetime,
        to_at: datetime,
        dimension: DistributionDimension,
        at: datetime,
    ) -> DistributionResponse:
        start, end, now = self._range(from_at, to_at, at)
        sessions = self.repository.all_sessions()
        size = 7 if dimension is DistributionDimension.WEEKDAY else 24
        totals = [0] * size
        cursor = start
        step = timedelta(days=1) if dimension is DistributionDimension.WEEKDAY else timedelta(hours=1)
        while cursor < end:
            local = cursor.astimezone(self.zone)
            if dimension is DistributionDimension.WEEKDAY:
                next_local = _local_midnight(local.date() + timedelta(days=1), self.zone)
                key = local.weekday()
            else:
                next_local = (local.replace(minute=0, second=0, microsecond=0) + step)
                key = local.hour
            next_cursor = min(end, next_local.astimezone(UTC))
            if next_cursor <= cursor:
                next_cursor = min(end, cursor + step)
            totals[key] += self._total(sessions, cursor, next_cursor, now)
            cursor = next_cursor
        labels = WEEKDAY_LABELS if dimension is DistributionDimension.WEEKDAY else tuple(
            datetime(2000, 1, 1, hour).strftime("%I %p").lstrip("0") for hour in range(24)
        )
        return DistributionResponse(
            from_at=start,
            to_at=end,
            time_zone=self.time_zone,
            dimension=dimension,
            buckets=[DistributionPoint(key=index, label=labels[index], total_seconds=value) for index, value in enumerate(totals)],
        )

    def game(self, game_id: int, *, from_at: datetime, to_at: datetime, at: datetime) -> GameAnalyticsResponse:
        game = self._require_game(game_id)
        start, end, now = self._range(from_at, to_at, at)
        sessions = [item for item in self.repository.all_sessions() if item.game_id == game_id]
        return GameAnalyticsResponse(
            game_id=game.id,
            game_title=game.title,
            from_at=start,
            to_at=end,
            time_zone=self.time_zone,
            summary=self._summary(sessions, start, end, now),
            daily_series=self._series(sessions, start, end, TimeBucket.DAY, now),
        )

    def _range(self, from_at: datetime, to_at: datetime, at: datetime) -> tuple[datetime, datetime, datetime]:
        start, end, now = _aware(from_at), _aware(to_at), _aware(at)
        if end <= start:
            raise InvalidSessionError("Analytics range end must be later than its start.")
        if end - start > MAX_RANGE:
            raise InvalidSessionError("Analytics range cannot exceed 366 days.")
        return start, end, now

    def _summary(self, sessions: list[GameSession], start: datetime, end: datetime, at: datetime) -> AnalyticsSummary:
        durations = [value for item in sessions if (value := clipped_seconds(item, start, end, at)) > 0]
        total = sum(durations)
        return AnalyticsSummary(
            total_seconds=total,
            session_count=len(durations),
            average_session_seconds=round(total / len(durations)) if durations else 0,
            longest_session_seconds=max(durations, default=0),
        )

    def _total(self, sessions: list[GameSession], start: datetime, end: datetime, at: datetime) -> int:
        return sum(clipped_seconds(item, start, end, at) for item in sessions)

    def _games(self, sessions: list[GameSession], start: datetime, end: datetime, at: datetime) -> list[GamePlaytime]:
        totals: dict[int, int] = defaultdict(int)
        counts: dict[int, int] = defaultdict(int)
        titles: dict[int, str] = {}
        for item in sessions:
            seconds = clipped_seconds(item, start, end, at)
            if seconds <= 0:
                continue
            totals[item.game_id] += seconds
            counts[item.game_id] += 1
            titles[item.game_id] = item.game.title
        return sorted(
            [GamePlaytime(game_id=game_id, game_title=titles[game_id], total_seconds=seconds, session_count=counts[game_id]) for game_id, seconds in totals.items()],
            key=lambda item: (-item.total_seconds, item.game_title.casefold()),
        )

    def _series(self, sessions: list[GameSession], start: datetime, end: datetime, bucket: TimeBucket, at: datetime) -> list[SeriesPoint]:
        local = start.astimezone(self.zone)
        if bucket is TimeBucket.DAY:
            cursor_date = local.date()
        elif bucket is TimeBucket.WEEK:
            cursor_date = local.date() - timedelta(days=(local.weekday() - self.week_starts_on) % 7)
        else:
            cursor_date = local.date().replace(day=1)
        points: list[SeriesPoint] = []
        while True:
            bucket_start = _local_midnight(cursor_date, self.zone).astimezone(UTC)
            if bucket_start >= end:
                break
            if bucket is TimeBucket.DAY:
                next_date = cursor_date + timedelta(days=1)
                label = cursor_date.strftime("%b %d").replace(" 0", " ")
            elif bucket is TimeBucket.WEEK:
                next_date = cursor_date + timedelta(days=7)
                label = f"Week of {cursor_date.strftime('%b %d')}"
            else:
                next_date = _next_month(cursor_date)
                label = cursor_date.strftime("%b %Y")
            bucket_end = _local_midnight(next_date, self.zone).astimezone(UTC)
            clipped_start, clipped_end = max(start, bucket_start), min(end, bucket_end)
            if clipped_end > clipped_start:
                points.append(SeriesPoint(
                    bucket_start=bucket_start,
                    label=label.replace(" 0", " "),
                    total_seconds=self._total(sessions, clipped_start, clipped_end, at),
                ))
            cursor_date = next_date
        return points

    def _require_game(self, game_id: int) -> Game:
        game = self.session.get(Game, game_id)
        if game is None:
            raise GameNotFoundError(f"Game {game_id} was not found.")
        return game

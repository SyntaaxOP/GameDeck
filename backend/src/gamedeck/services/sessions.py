"""Gaming session business rules and state transitions."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gamedeck.domain.errors import (
    ActiveSessionMutationError,
    GameArchivedError,
    GameNotFoundError,
    InvalidSessionError,
    SessionNotFoundError,
    SessionOverlapError,
)
from gamedeck.models.game import Game
from gamedeck.models.game_session import GameSession
from gamedeck.repositories.sessions import SessionRepository
from gamedeck.schemas.session import (
    EndReason,
    ManualSessionCreate,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)
from gamedeck.services.games import utc_now


def to_utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise InvalidSessionError("Timestamp must include a UTC offset or timezone.")
    return value.astimezone(UTC).replace(tzinfo=None)


def as_utc(value: datetime | None) -> datetime | None:
    return value.replace(tzinfo=UTC) if value is not None else None


def calculate_duration(
    started_at: datetime, ended_at: datetime, *, allow_zero: bool = False
) -> int:
    seconds = int((ended_at - started_at).total_seconds())
    if seconds < 0 or (seconds == 0 and not allow_zero):
        raise InvalidSessionError("Session end must be later than its start.")
    return seconds


class SessionService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = SessionRepository(session)

    def create_manual(self, payload: ManualSessionCreate) -> GameSession:
        game = self._get_game(payload.game_id)
        if game.archived_at is not None:
            raise GameArchivedError("Restore this game before adding a session.")
        started_at = to_utc_naive(payload.started_at)
        ended_at = to_utc_naive(payload.ended_at)
        duration = calculate_duration(started_at, ended_at)
        self._reject_overlap(game.id, started_at, ended_at)
        now = utc_now()
        game_session = GameSession(
            game_id=game.id,
            started_at=started_at,
            ended_at=ended_at,
            last_seen_at=ended_at,
            duration_seconds=duration,
            detection_method="manual",
            end_reason="manual",
            created_at=now,
            updated_at=now,
        )
        self.repository.add(game_session)
        self.session.commit()
        return self.get(game_session.id)

    def update(self, session_id: int, payload: SessionUpdate) -> GameSession:
        game_session = self.get(session_id)
        if game_session.ended_at is None:
            raise ActiveSessionMutationError("Active sessions cannot be edited manually.")
        values = payload.model_dump(exclude_unset=True)
        if not values:
            return game_session
        started_at = to_utc_naive(values.get("started_at", as_utc(game_session.started_at)))
        ended_at = to_utc_naive(values.get("ended_at", as_utc(game_session.ended_at)))
        duration = calculate_duration(started_at, ended_at)
        self._reject_overlap(
            game_session.game_id,
            started_at,
            ended_at,
            exclude_session_id=game_session.id,
        )
        game_session.started_at = started_at
        game_session.ended_at = ended_at
        game_session.last_seen_at = ended_at
        game_session.duration_seconds = duration
        game_session.updated_at = utc_now()
        self.session.commit()
        return self.get(game_session.id)

    def delete(self, session_id: int) -> None:
        game_session = self.get(session_id)
        if game_session.ended_at is None:
            raise ActiveSessionMutationError("Active sessions cannot be deleted manually.")
        self.repository.delete(game_session)
        self.session.commit()

    def get(self, session_id: int) -> GameSession:
        game_session = self.repository.get(session_id)
        if game_session is None:
            raise SessionNotFoundError(f"Session {session_id} was not found.")
        return game_session

    def list(
        self,
        *,
        game_id: int | None,
        from_at: datetime | None,
        to_at: datetime | None,
        active: bool | None,
        page: int,
        page_size: int,
    ) -> SessionListResponse:
        normalized_from = to_utc_naive(from_at) if from_at is not None else None
        normalized_to = to_utc_naive(to_at) if to_at is not None else None
        if normalized_from and normalized_to and normalized_to <= normalized_from:
            raise InvalidSessionError("The end of the filter range must be after its start.")
        sessions, total = self.repository.list(
            game_id=game_id,
            from_at=normalized_from,
            to_at=normalized_to,
            active=active,
            page=page,
            page_size=page_size,
        )
        return SessionListResponse(
            items=[self.to_response(item) for item in sessions],
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_active(self) -> list[SessionResponse]:
        return [self.to_response(item) for item in self.repository.list_active()]

    def start_process_session(
        self,
        game_id: int,
        *,
        observed_at: datetime,
        process_id: int | None = None,
        process_started_at: datetime | None = None,
    ) -> GameSession:
        game = self._get_game(game_id)
        if game.archived_at is not None:
            raise GameArchivedError("Archived games cannot start tracked sessions.")
        observed = to_utc_naive(observed_at)
        active = self.repository.get_active(game_id)
        if active is not None:
            active.last_seen_at = max(active.last_seen_at, observed)
            active.process_id = process_id
            active.process_started_at = (
                to_utc_naive(process_started_at) if process_started_at is not None else None
            )
            active.updated_at = utc_now()
            self.session.commit()
            return self.get(active.id)

        now = utc_now()
        game_session = GameSession(
            game_id=game_id,
            started_at=observed,
            ended_at=None,
            last_seen_at=observed,
            duration_seconds=None,
            detection_method="process",
            end_reason=None,
            process_id=process_id,
            process_started_at=(
                to_utc_naive(process_started_at) if process_started_at is not None else None
            ),
            created_at=now,
            updated_at=now,
        )
        try:
            self.repository.add(game_session)
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            winner = self.repository.get_active(game_id)
            if winner is None:
                raise
            return winner
        return self.get(game_session.id)

    def end_active_session(
        self,
        game_id: int,
        *,
        ended_at: datetime | None = None,
        reason: EndReason = EndReason.PROCESS_STOPPED,
    ) -> GameSession | None:
        active = self.repository.get_active(game_id)
        if active is None:
            return None
        end = to_utc_naive(ended_at) if ended_at is not None else active.last_seen_at
        duration = calculate_duration(active.started_at, end, allow_zero=True)
        active.ended_at = end
        active.last_seen_at = end
        active.duration_seconds = duration
        active.end_reason = reason.value
        active.updated_at = utc_now()
        self.session.commit()
        return self.get(active.id)

    def to_response(self, game_session: GameSession) -> SessionResponse:
        return SessionResponse(
            id=game_session.id,
            game_id=game_session.game_id,
            game_title=game_session.game.title,
            started_at=as_utc(game_session.started_at),
            ended_at=as_utc(game_session.ended_at),
            last_seen_at=as_utc(game_session.last_seen_at),
            duration_seconds=game_session.duration_seconds,
            detection_method=game_session.detection_method,
            end_reason=game_session.end_reason,
            active=game_session.ended_at is None,
            created_at=as_utc(game_session.created_at),
            updated_at=as_utc(game_session.updated_at),
        )

    def _get_game(self, game_id: int) -> Game:
        game = self.session.get(Game, game_id)
        if game is None:
            raise GameNotFoundError(f"Game {game_id} was not found.")
        return game

    def _reject_overlap(
        self,
        game_id: int,
        started_at: datetime,
        ended_at: datetime,
        *,
        exclude_session_id: int | None = None,
    ) -> None:
        if self.repository.overlaps(
            game_id=game_id,
            started_at=started_at,
            ended_at=ended_at,
            exclude_session_id=exclude_session_id,
        ):
            raise SessionOverlapError("This session overlaps another session for the same game.")

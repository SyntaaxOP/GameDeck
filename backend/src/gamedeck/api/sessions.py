"""Gaming session HTTP routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.session import (
    ManualSessionCreate,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)
from gamedeck.services.sessions import SessionService


router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
DatabaseSession = Annotated[Session, Depends(get_db_session)]


@router.get("", response_model=SessionListResponse)
def list_sessions(
    session: DatabaseSession,
    game_id: Annotated[int | None, Query(gt=0)] = None,
    from_at: Annotated[datetime | None, Query(alias="from")] = None,
    to_at: Annotated[datetime | None, Query(alias="to")] = None,
    active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> SessionListResponse:
    return SessionService(session).list(
        game_id=game_id,
        from_at=from_at,
        to_at=to_at,
        active=active,
        page=page,
        page_size=page_size,
    )


@router.get("/active", response_model=list[SessionResponse])
def list_active_sessions(session: DatabaseSession) -> list[SessionResponse]:
    return SessionService(session).list_active()


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_manual_session(
    payload: ManualSessionCreate, session: DatabaseSession
) -> SessionResponse:
    service = SessionService(session)
    return service.to_response(service.create_manual(payload))


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, session: DatabaseSession) -> SessionResponse:
    service = SessionService(session)
    return service.to_response(service.get(session_id))


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int, payload: SessionUpdate, session: DatabaseSession
) -> SessionResponse:
    service = SessionService(session)
    return service.to_response(service.update(session_id, payload))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: int, session: DatabaseSession) -> Response:
    SessionService(session).delete(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


"""Manual FiveM companion routes."""

from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.fivem import FiveMServerCreate, FiveMServerListResponse, FiveMServerResponse, FiveMServerUpdate
from gamedeck.services.fivem import FiveMService

router = APIRouter(prefix="/api/v1/fivem/servers", tags=["fivem"])
DatabaseSession = Annotated[Session, Depends(get_db_session)]


@router.get("", response_model=FiveMServerListResponse)
def list_servers(session: DatabaseSession) -> FiveMServerListResponse:
    return FiveMService(session).list()


@router.post("", response_model=FiveMServerResponse, status_code=status.HTTP_201_CREATED)
def create_server(payload: FiveMServerCreate, session: DatabaseSession) -> FiveMServerResponse:
    return FiveMService(session).create(payload)


@router.patch("/{server_id}", response_model=FiveMServerResponse)
def update_server(server_id: int, payload: FiveMServerUpdate, session: DatabaseSession) -> FiveMServerResponse:
    return FiveMService(session).update(server_id, payload)


@router.post("/{server_id}/joined", response_model=FiveMServerResponse)
def mark_joined(server_id: int, session: DatabaseSession) -> FiveMServerResponse:
    return FiveMService(session).mark_joined(server_id)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(server_id: int, session: DatabaseSession) -> Response:
    FiveMService(session).delete(server_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

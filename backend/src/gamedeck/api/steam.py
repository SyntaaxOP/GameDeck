"""Steam online and local-install endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.steam import (
    SteamConfigurationResponse,
    SteamImportRequest,
    SteamImportResponse,
    SteamLocalLibraryResponse,
    SteamLocalSyncResponse,
    SteamPreviewRequest,
    SteamPreviewResponse,
)
from gamedeck.services.steam import SteamService


router = APIRouter(prefix="/api/v1/steam", tags=["steam"])
DatabaseSession = Annotated[Session, Depends(get_db_session)]


def service(request: Request, session: Session) -> SteamService:
    return SteamService(session, request.app.state.settings)


@router.get("/configuration", response_model=SteamConfigurationResponse)
def configuration(request: Request, session: DatabaseSession) -> SteamConfigurationResponse:
    return service(request, session).configuration()


@router.get("/local-library", response_model=SteamLocalLibraryResponse)
def local_library(request: Request, session: DatabaseSession) -> SteamLocalLibraryResponse:
    return service(request, session).local_library()


@router.post("/local-library/sync", response_model=SteamLocalSyncResponse)
def sync_local_library(request: Request, session: DatabaseSession) -> SteamLocalSyncResponse:
    return service(request, session).sync_local_library()


@router.post("/preview", response_model=SteamPreviewResponse)
def preview(
    payload: SteamPreviewRequest,
    request: Request,
    session: DatabaseSession,
) -> SteamPreviewResponse:
    return service(request, session).preview(payload.steam_id)


@router.post("/import", response_model=SteamImportResponse)
def import_games(
    payload: SteamImportRequest,
    request: Request,
    session: DatabaseSession,
) -> SteamImportResponse:
    return service(request, session).import_games(payload)

"""Local operations and diagnostics API."""

from fastapi import APIRouter, Request, status

from gamedeck.schemas.system import BackupResponse, DiagnosticsResponse
from gamedeck.services.system import SystemService


router = APIRouter(prefix="/api/v1/system", tags=["system"])


def service(request: Request) -> SystemService:
    return SystemService(request.app.state.database, request.app.state.settings)


@router.get("/diagnostics", response_model=DiagnosticsResponse)
def diagnostics(request: Request) -> DiagnosticsResponse:
    return service(request).diagnostics()


@router.get("/backups", response_model=list[BackupResponse])
def list_backups(request: Request) -> list[BackupResponse]:
    return service(request).list_backups()


@router.post("/backups", response_model=BackupResponse, status_code=status.HTTP_201_CREATED)
def create_backup(request: Request) -> BackupResponse:
    return service(request).create_backup()

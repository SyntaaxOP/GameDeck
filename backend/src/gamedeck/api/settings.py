"""Application settings API."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.settings import SettingsResponse, SettingsUpdate
from gamedeck.services.settings import SettingsService


router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings(session: Session = Depends(get_db_session)) -> SettingsResponse:
    return SettingsService(session).get()


@router.patch("", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdate,
    request: Request,
    session: Session = Depends(get_db_session),
) -> SettingsResponse:
    result = SettingsService(session).update(payload)
    request.app.state.monitor.configuration_changed(
        enabled=result.tracking_enabled,
        scan_interval_seconds=result.scan_interval_seconds,
        restart_grace_seconds=result.restart_grace_seconds,
    )
    return result

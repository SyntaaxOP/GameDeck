"""Process tracker status API."""

from fastapi import APIRouter, Request

from gamedeck.schemas.settings import TrackerStatusResponse


router = APIRouter(prefix="/api/v1/tracker", tags=["tracker"])


@router.get("/status", response_model=TrackerStatusResponse)
def tracker_status(request: Request) -> TrackerStatusResponse:
    return request.app.state.monitor.status()

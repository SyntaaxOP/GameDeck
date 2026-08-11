from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.detection import DetectionConfirmRequest, DetectionReviewResponse, IgnoredExecutableListResponse
from gamedeck.schemas.game import GameResponse
from gamedeck.services.detections import DetectionService

router = APIRouter(prefix="/api/v1/detections", tags=["detections"])
DB = Annotated[Session, Depends(get_db_session)]

@router.get("", response_model=DetectionReviewResponse)
def pending(session: DB) -> DetectionReviewResponse: return DetectionService(session).pending()

@router.post("/{game_id}/confirm", response_model=GameResponse)
def confirm(game_id: int, payload: DetectionConfirmRequest, session: DB) -> GameResponse: return DetectionService(session).confirm(game_id, payload.title)

@router.post("/{game_id}/ignore", status_code=status.HTTP_204_NO_CONTENT)
def ignore(game_id: int, session: DB) -> Response:
    DetectionService(session).ignore(game_id); return Response(status_code=204)

@router.get("/ignored", response_model=IgnoredExecutableListResponse)
def ignored(session: DB) -> IgnoredExecutableListResponse: return DetectionService(session).ignored()

@router.delete("/ignored/{ignored_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_ignored(ignored_id: int, session: DB) -> Response:
    DetectionService(session).remove_ignored(ignored_id); return Response(status_code=204)

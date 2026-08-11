from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.game_night import DiscordAnnouncementResponse, GameNightCreate, GameNightListResponse, GameNightResponse, GameNightUpdate
from gamedeck.services.game_nights import GameNightService
router=APIRouter(prefix="/api/v1/game-nights",tags=["game nights"]); DatabaseSession=Annotated[Session,Depends(get_db_session)]
@router.get("",response_model=GameNightListResponse)
def list_nights(session:DatabaseSession): return GameNightService(session).list()
@router.post("",response_model=GameNightResponse,status_code=status.HTTP_201_CREATED)
def create_night(payload:GameNightCreate,session:DatabaseSession): return GameNightService(session).create(payload)
@router.patch("/{night_id}",response_model=GameNightResponse)
def update_night(night_id:int,payload:GameNightUpdate,session:DatabaseSession): return GameNightService(session).update(night_id,payload)
@router.delete("/{night_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_night(night_id:int,session:DatabaseSession): GameNightService(session).delete(night_id); return Response(status_code=204)
@router.get("/{night_id}/discord-announcement",response_model=DiscordAnnouncementResponse)
def announcement(night_id:int,session:DatabaseSession): return GameNightService(session).announcement(night_id)

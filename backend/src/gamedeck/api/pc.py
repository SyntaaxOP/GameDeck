from typing import Annotated
from fastapi import APIRouter,Depends,Response
from sqlalchemy.orm import Session
from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.pc import PCProfileResponse,PCProfileUpdate,PCSnapshotResponse
from gamedeck.services.pc import PCService
router=APIRouter(prefix="/api/v1/pc",tags=["pc profile"]);DB=Annotated[Session,Depends(get_db_session)]
@router.get("/profile",response_model=PCProfileResponse|None)
def profile(session:DB):return PCService(session).get()
@router.put("/profile",response_model=PCProfileResponse)
def save(payload:PCProfileUpdate,session:DB):return PCService(session).update(payload)
@router.get("/snapshot",response_model=PCSnapshotResponse)
def snapshot(session:DB):return PCService(session).snapshot()

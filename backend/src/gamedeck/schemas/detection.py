from datetime import datetime
from pydantic import BaseModel, Field
from gamedeck.schemas.game import GameResponse

class DetectionReviewResponse(BaseModel):
    items: list[GameResponse]
    total: int

class DetectionConfirmRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)

class IgnoredExecutableResponse(BaseModel):
    id: int
    executable_name: str
    executable_path: str | None
    created_at: datetime

class IgnoredExecutableListResponse(BaseModel):
    items: list[IgnoredExecutableResponse]
    total: int

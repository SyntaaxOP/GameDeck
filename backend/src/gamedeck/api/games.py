"""Game library HTTP routes."""

from typing import Annotated, Literal

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from gamedeck.api.dependencies import get_db_session
from gamedeck.schemas.game import (
    GameCreate,
    GameListResponse,
    GameResponse,
    GameSort,
    GameUpdate,
    LibraryStatus,
    Platform,
)
from gamedeck.services.games import GameService
from gamedeck.services.launcher import GameLauncher


router = APIRouter(prefix="/api/v1/games", tags=["games"])
DatabaseSession = Annotated[Session, Depends(get_db_session)]


@router.get("", response_model=GameListResponse)
def list_games(
    session: DatabaseSession,
    q: Annotated[str | None, Query(max_length=200)] = None,
    platform: Platform | None = None,
    library_status: Annotated[LibraryStatus | None, Query(alias="status")] = None,
    favorite: bool | None = None,
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
    archived: bool = False,
    sort: GameSort = GameSort.TITLE,
    order: Literal["asc", "desc"] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> GameListResponse:
    return GameService(session).list(
        query=q,
        platform=platform,
        status=library_status,
        favorite=favorite,
        priority=priority,
        archived=archived,
        sort=sort,
        descending=order == "desc",
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
def create_game(payload: GameCreate, session: DatabaseSession) -> GameResponse:
    return GameResponse.model_validate(GameService(session).create(payload))


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: int, session: DatabaseSession) -> GameResponse:
    return GameResponse.model_validate(GameService(session).get(game_id))


@router.get("/{game_id}/cover", response_class=FileResponse)
def get_game_cover(game_id: int, session: DatabaseSession) -> FileResponse:
    game = GameService(session).get(game_id)
    artwork = Path(game.cover_path) if game.cover_path else None
    if artwork is None or not artwork.is_file() or artwork.suffix.casefold() not in {".jpg", ".jpeg", ".png"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artwork is unavailable.")
    media_type = "image/png" if artwork.suffix.casefold() == ".png" else "image/jpeg"
    return FileResponse(
        artwork,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.patch("/{game_id}", response_model=GameResponse)
def update_game(game_id: int, payload: GameUpdate, session: DatabaseSession) -> GameResponse:
    return GameResponse.model_validate(GameService(session).update(game_id, payload))


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_game(game_id: int, session: DatabaseSession) -> Response:
    GameService(session).archive(game_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{game_id}/restore", response_model=GameResponse)
def restore_game(game_id: int, session: DatabaseSession) -> GameResponse:
    return GameResponse.model_validate(GameService(session).restore(game_id))

@router.post("/{game_id}/launch", status_code=status.HTTP_204_NO_CONTENT)
def launch_game(game_id: int, session: DatabaseSession) -> Response:
    GameLauncher(session).launch(game_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

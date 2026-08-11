import ntpath
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from gamedeck.models.game import Game
from gamedeck.models.ignored_executable import IgnoredExecutable
from gamedeck.schemas.detection import DetectionReviewResponse, IgnoredExecutableListResponse, IgnoredExecutableResponse
from gamedeck.schemas.game import GameResponse, GameUpdate
from gamedeck.services.games import GameService, utc_now

AUTO_NOTE = "Automatically detected from sustained foreground game activity."
CONFIRMED_NOTE = "Confirmed automatic game detection."

class DetectionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def pending(self) -> DetectionReviewResponse:
        games = list(self.session.scalars(select(Game).options(selectinload(Game.executable_mappings)).where(Game.archived_at.is_(None), Game.notes == AUTO_NOTE).order_by(Game.discovered_at.desc())))
        return DetectionReviewResponse(items=[GameResponse.model_validate(game) for game in games], total=len(games))

    def confirm(self, game_id: int, title: str | None) -> GameResponse:
        game = GameService(self.session).get(game_id)
        payload = GameUpdate(notes=CONFIRMED_NOTE, **({"title": title} if title else {}))
        return GameResponse.model_validate(GameService(self.session).update(game_id, payload))

    def ignore(self, game_id: int) -> None:
        game = GameService(self.session).get(game_id)
        path = ntpath.normcase(ntpath.normpath(game.executable_path)) if game.executable_path else None
        existing = self.session.scalar(select(IgnoredExecutable).where(IgnoredExecutable.executable_path == path)) if path else None
        if existing is None:
            self.session.add(IgnoredExecutable(executable_name=game.executable_name.casefold(), executable_path=path, created_at=utc_now()))
            self.session.commit()
        GameService(self.session).archive(game_id)

    def ignored(self) -> IgnoredExecutableListResponse:
        items = list(self.session.scalars(select(IgnoredExecutable).order_by(IgnoredExecutable.created_at.desc())))
        return IgnoredExecutableListResponse(items=[IgnoredExecutableResponse.model_validate(item, from_attributes=True) for item in items], total=len(items))

    def remove_ignored(self, ignored_id: int) -> None:
        item = self.session.get(IgnoredExecutable, ignored_id)
        if item is not None:
            self.session.delete(item)
            self.session.commit()

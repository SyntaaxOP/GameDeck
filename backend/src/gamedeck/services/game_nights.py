"""Local game-night planning and Discord-ready announcements."""
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from gamedeck.domain.errors import GameNightNotFoundError, GameNotFoundError
from gamedeck.models.game import Game
from gamedeck.models.game_night import GameNight, GameNightAttendee
from gamedeck.schemas.game_night import DiscordAnnouncementResponse, GameNightCreate, GameNightListResponse, GameNightResponse, GameNightUpdate
from gamedeck.services.games import utc_now

class GameNightService:
    def __init__(self, session: Session): self.session=session
    def get_model(self, night_id: int) -> GameNight:
        item=self.session.scalar(select(GameNight).options(selectinload(GameNight.attendees), selectinload(GameNight.game)).where(GameNight.id==night_id))
        if item is None: raise GameNightNotFoundError(f"Game night {night_id} was not found.")
        return item
    def list(self) -> GameNightListResponse:
        items=list(self.session.scalars(select(GameNight).options(selectinload(GameNight.attendees), selectinload(GameNight.game)).order_by(GameNight.scheduled_at.desc())))
        return GameNightListResponse(items=[self.response(item) for item in items], total=len(items))
    def create(self, payload: GameNightCreate) -> GameNightResponse:
        values=payload.model_dump(mode="python"); attendees=values.pop("attendees"); self._game(values.get("game_id")); now=utc_now()
        item=GameNight(**values, created_at=now, updated_at=now); self.session.add(item); self.session.flush(); self._replace(item, attendees); self.session.commit()
        return self.response(self.get_model(item.id))
    def update(self, night_id: int, payload: GameNightUpdate) -> GameNightResponse:
        item=self.get_model(night_id); values=payload.model_dump(exclude_unset=True, mode="python"); attendees=values.pop("attendees", None)
        if "game_id" in values: self._game(values["game_id"])
        for key,value in values.items(): setattr(item,key,value.value if hasattr(value,"value") else value)
        if attendees is not None: self._replace(item, attendees)
        if values or attendees is not None: item.updated_at=utc_now(); self.session.commit()
        return self.response(self.get_model(night_id))
    def delete(self, night_id: int): self.session.delete(self.get_model(night_id)); self.session.commit()
    def announcement(self, night_id: int) -> DiscordAnnouncementResponse:
        item=self.get_model(night_id); confirmed=[a.name for a in item.attendees if a.response=="confirmed"]; maybe=[a.name for a in item.attendees if a.response=="maybe"]
        lines=["🎮 GAME NIGHT", "", item.title, f"When: {item.scheduled_at.isoformat(sep=' ', timespec='minutes')} UTC", f"Duration: {item.duration_minutes} minutes"]
        if item.game: lines.append(f"Game: {item.game.title}")
        lines.extend([f"Confirmed ({len(confirmed)}): {', '.join(confirmed) or 'None yet'}", f"Maybe ({len(maybe)}): {', '.join(maybe) or 'None'}"])
        if item.notes: lines.extend(["", item.notes])
        return DiscordAnnouncementResponse(message="\n".join(lines))
    def _replace(self, item: GameNight, attendees: list[dict[str, object]]):
        item.attendees.clear(); self.session.flush()
        item.attendees.extend(GameNightAttendee(name=str(a["name"]), response=a["response"].value if hasattr(a["response"],"value") else str(a["response"])) for a in attendees)
    def _game(self, game_id: object):
        if game_id is not None and self.session.get(Game, int(game_id)) is None: raise GameNotFoundError(f"Game {game_id} was not found.")
    @staticmethod
    def response(item: GameNight) -> GameNightResponse:
        return GameNightResponse(id=item.id,title=item.title,game_id=item.game_id,game_title=item.game.title if item.game else None,scheduled_at=item.scheduled_at,duration_minutes=item.duration_minutes,status=item.status,notes=item.notes,attendees=[{"id":a.id,"name":a.name,"response":a.response} for a in item.attendees],created_at=item.created_at,updated_at=item.updated_at)

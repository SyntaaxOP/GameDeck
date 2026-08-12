"""Game library business rules."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import PureWindowsPath
from pathlib import Path

from sqlalchemy import delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gamedeck.domain.errors import (
    ExecutableConflictError,
    GameNotFoundError,
    InvalidGamePathError,
)
from gamedeck.models.game import Game
from gamedeck.models.game_executable import GameExecutable
from gamedeck.models.game_night import GameNight
from gamedeck.models.game_session import GameSession
from gamedeck.models.purchase import Purchase
from gamedeck.repositories.games import GameRepository
from gamedeck.schemas.game import (
    GameCreate,
    GameListResponse,
    GameResponse,
    GameSort,
    GameUpdate,
    LibraryStatus,
    Platform,
    validate_windows_path,
)


COMPLETED_STATUSES = {LibraryStatus.COMPLETED.value, LibraryStatus.COMPLETED_100.value}
NON_QUEUE_STATUSES = COMPLETED_STATUSES | {LibraryStatus.DROPPED.value}


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class GameService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = GameRepository(session)

    def create(self, payload: GameCreate) -> Game:
        values = payload.model_dump(mode="python")
        aliases = values.pop("executable_aliases")
        self._normalize_and_validate_paths(values)
        self._apply_completion_rule(values)
        self._apply_queue_rule(values)
        now = utc_now()
        game = Game(
            **values,
            date_added=now,
            created_at=now,
            updated_at=now,
        )
        try:
            self.repository.add(game)
            self._create_mappings(game, aliases, now)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ExecutableConflictError(
                "That executable is already assigned to another active game."
            ) from exc
        self.session.refresh(game)
        return game

    def get(self, game_id: int) -> Game:
        game = self.repository.get(game_id)
        if game is None:
            raise GameNotFoundError(f"Game {game_id} was not found.")
        return game

    def list(
        self,
        *,
        query: str | None,
        platform: Platform | None,
        status: LibraryStatus | None,
        favorite: bool | None,
        priority: int | None,
        archived: bool,
        sort: GameSort,
        descending: bool,
        page: int,
        page_size: int,
    ) -> GameListResponse:
        games, total = self.repository.list(
            query=query,
            platform=platform,
            status=status,
            favorite=favorite,
            priority=priority,
            archived=archived,
            sort=sort,
            descending=descending,
            page=page,
            page_size=page_size,
        )
        return GameListResponse(
            items=[GameResponse.model_validate(game) for game in games],
            total=total,
            page=page,
            page_size=page_size,
        )

    def update(self, game_id: int, payload: GameUpdate) -> Game:
        game = self.get(game_id)
        values = payload.model_dump(exclude_unset=True, mode="python")
        if not values:
            return game
        aliases = values.pop("executable_aliases", None)
        self._normalize_and_validate_paths(values, existing=game)
        self._validate_mapping_names(game, values, aliases)
        self._apply_completion_rule(values, existing=game)
        self._apply_queue_rule(values, existing=game)
        for field, value in values.items():
            setattr(game, field, value.value if hasattr(value, "value") else value)
        game.updated_at = utc_now()
        try:
            self._sync_primary_mapping(game)
            if aliases is not None:
                self._replace_aliases(game, aliases)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ExecutableConflictError(
                "That executable is already assigned to another active game."
            ) from exc
        self.session.refresh(game)
        return game

    def archive(self, game_id: int) -> None:
        game = self.get(game_id)
        if game.archived_at is None:
            game.archived_at = utc_now()
            game.updated_at = game.archived_at
            for mapping in game.executable_mappings:
                mapping.active = False
                mapping.updated_at = game.updated_at
            self.session.commit()

    def restore(self, game_id: int) -> Game:
        game = self.get(game_id)
        if game.archived_at is None:
            return game
        game.archived_at = None
        game.updated_at = utc_now()
        for mapping in game.executable_mappings:
            mapping.active = True
            mapping.updated_at = game.updated_at
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise ExecutableConflictError(
                "Another active game now uses this executable. Update it before restoring."
            ) from exc
        self.session.refresh(game)
        return game

    def delete_permanently(self, game_id: int) -> None:
        game = self.get(game_id)
        artwork = Path(game.cover_path) if game.cover_path else None
        self.session.execute(delete(GameSession).where(GameSession.game_id == game_id))
        self.session.execute(update(Purchase).where(Purchase.game_id == game_id).values(game_id=None))
        self.session.execute(update(GameNight).where(GameNight.game_id == game_id).values(game_id=None))
        self.session.delete(game)
        self.session.commit()
        if artwork is not None:
            try:
                if artwork.is_file() and artwork.parent.name.casefold() == "artwork":
                    artwork.unlink()
            except OSError:
                pass

    def _create_mappings(
        self, game: Game, aliases: list[dict[str, object]], now: datetime
    ) -> None:
        self.session.add(
            GameExecutable(
                game=game,
                executable_name=game.executable_name,
                executable_path=game.executable_path,
                is_primary=True,
                active=game.archived_at is None,
                created_at=now,
                updated_at=now,
            )
        )
        for alias in aliases:
            self.session.add(
                GameExecutable(
                    game=game,
                    executable_name=str(alias["executable_name"]),
                    executable_path=alias.get("executable_path"),
                    is_primary=False,
                    active=game.archived_at is None,
                    created_at=now,
                    updated_at=now,
                )
            )

    def _sync_primary_mapping(self, game: Game) -> None:
        primary = next(
            (mapping for mapping in game.executable_mappings if mapping.is_primary), None
        )
        if primary is None:
            self._create_mappings(game, [], game.updated_at)
            return
        primary.executable_name = game.executable_name
        primary.executable_path = game.executable_path
        primary.active = game.archived_at is None
        primary.updated_at = game.updated_at

    def _replace_aliases(self, game: Game, aliases: list[dict[str, object]]) -> None:
        for mapping in list(game.executable_mappings):
            if not mapping.is_primary:
                self.session.delete(mapping)
        self.session.flush()
        now = game.updated_at
        for alias in aliases:
            self.session.add(
                GameExecutable(
                    game=game,
                    executable_name=str(alias["executable_name"]),
                    executable_path=alias.get("executable_path"),
                    is_primary=False,
                    active=game.archived_at is None,
                    created_at=now,
                    updated_at=now,
                )
            )

    @staticmethod
    def _validate_mapping_names(
        game: Game,
        values: dict[str, object],
        aliases: list[dict[str, object]] | None,
    ) -> None:
        primary_name = str(values.get("executable_name", game.executable_name)).lower()
        alias_names = (
            [str(alias["executable_name"]).lower() for alias in aliases]
            if aliases is not None
            else [mapping.executable_name.lower() for mapping in game.executable_aliases]
        )
        names = [primary_name, *alias_names]
        if len(names) != len(set(names)):
            raise ExecutableConflictError(
                "Primary and alias executable names must be distinct."
            )

    def _normalize_and_validate_paths(
        self, values: dict[str, object], *, existing: Game | None = None
    ) -> None:
        executable_name = str(values.get("executable_name") or existing.executable_name).lower() if existing else str(values["executable_name"]).lower()
        try:
            if "executable_path" in values:
                path = validate_windows_path(
                    values["executable_path"] if isinstance(values["executable_path"], str) else None,
                    field_name="Executable path",
                )
                values["executable_path"] = path
            else:
                path = existing.executable_path if existing else None
            if "cover_path" in values:
                values["cover_path"] = validate_windows_path(
                    values["cover_path"] if isinstance(values["cover_path"], str) else None,
                    field_name="Cover path",
                )
        except ValueError as exc:
            raise InvalidGamePathError(str(exc)) from exc
        if path and PureWindowsPath(path).name.lower() != executable_name:
            raise InvalidGamePathError(
                "Executable path filename must match the configured executable name."
            )

    @staticmethod
    def _apply_completion_rule(values: dict[str, object], existing: Game | None = None) -> None:
        status_value = values.get("status", existing.status if existing else LibraryStatus.BACKLOG.value)
        status_text = status_value.value if hasattr(status_value, "value") else str(status_value)
        if status_text in COMPLETED_STATUSES:
            if values.get("date_completed") is None and (not existing or existing.date_completed is None):
                values["date_completed"] = date.today()
        elif "status" in values:
            values["date_completed"] = None

    @staticmethod
    def _apply_queue_rule(values: dict[str, object], existing: Game | None = None) -> None:
        status_value = values.get("status", existing.status if existing else LibraryStatus.BACKLOG.value)
        status_text = status_value.value if hasattr(status_value, "value") else str(status_value)
        if status_text in NON_QUEUE_STATUSES:
            values["priority"] = None

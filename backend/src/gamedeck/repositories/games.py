"""Database access for the game library."""

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from gamedeck.models.game import Game
from gamedeck.schemas.game import GameSort, LibraryStatus, Platform


class GameRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, game: Game) -> Game:
        self.session.add(game)
        self.session.flush()
        return game

    def get(self, game_id: int) -> Game | None:
        statement = select(Game).options(selectinload(Game.executable_mappings)).where(Game.id == game_id)
        return self.session.scalar(statement)

    def find_active_by_executable(self, executable_name: str) -> Game | None:
        statement = select(Game).where(
            func.lower(Game.executable_name) == executable_name.lower(),
            Game.archived_at.is_(None),
        )
        return self.session.scalar(statement)

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
    ) -> tuple[list[Game], int]:
        statement: Select[tuple[Game]] = select(Game).options(selectinload(Game.executable_mappings))
        count_statement = select(func.count()).select_from(Game)
        filters = [Game.archived_at.is_not(None) if archived else Game.archived_at.is_(None)]
        if query:
            escaped = query.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            filters.append(func.lower(Game.title).like(f"%{escaped}%", escape="\\"))
        if platform is not None:
            filters.append(Game.platform == platform.value)
        if status is not None:
            filters.append(Game.status == status.value)
        if favorite is not None:
            filters.append(Game.favorite == favorite)
        if priority is not None:
            filters.append(Game.priority == priority)

        sort_columns = {
            GameSort.TITLE: func.lower(Game.title),
            GameSort.DATE_ADDED: Game.date_added,
            GameSort.UPDATED_AT: Game.updated_at,
            GameSort.STATUS: Game.status,
            GameSort.PRIORITY: Game.priority,
        }
        if sort is GameSort.PLAY_NEXT:
            ordering = (
                Game.status.in_((
                    LibraryStatus.CURRENTLY_PLAYING.value,
                    LibraryStatus.BACKLOG.value,
                    LibraryStatus.PAUSED.value,
                )).desc(),
                Game.favorite.desc(),
                Game.priority.is_(None).asc(),
                Game.priority.asc(),
                Game.updated_at.desc(),
                func.lower(Game.title).asc(),
            )
        else:
            sort_column = sort_columns[sort]
            direction = sort_column.desc() if descending else sort_column.asc()
            if sort is GameSort.PRIORITY:
                ordering = (Game.priority.is_(None).asc(), direction, func.lower(Game.title).asc())
            else:
                ordering = (direction, Game.id.asc())

        statement = (
            statement.where(*filters)
            .order_by(*ordering)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = count_statement.where(*filters)
        return list(self.session.scalars(statement)), int(self.session.scalar(count_statement) or 0)

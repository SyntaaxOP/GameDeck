"""Manual FiveM server companion rules."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from gamedeck.domain.errors import FiveMServerConflictError, FiveMServerNotFoundError
from gamedeck.models.fivem_server import FiveMServer
from gamedeck.schemas.fivem import FiveMServerCreate, FiveMServerListResponse, FiveMServerResponse, FiveMServerUpdate
from gamedeck.services.games import utc_now


class FiveMService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_model(self, server_id: int) -> FiveMServer:
        server = self.session.get(FiveMServer, server_id)
        if server is None:
            raise FiveMServerNotFoundError(f"FiveM server {server_id} was not found.")
        return server

    def list(self) -> FiveMServerListResponse:
        statement = select(FiveMServer).order_by(
            FiveMServer.favorite.desc(), FiveMServer.last_joined_at.desc(), func.lower(FiveMServer.name)
        )
        items = list(self.session.scalars(statement))
        return FiveMServerListResponse(items=items, total=len(items))

    def create(self, payload: FiveMServerCreate) -> FiveMServerResponse:
        now = utc_now()
        server = FiveMServer(**payload.model_dump(mode="python"), created_at=now, updated_at=now)
        self.session.add(server)
        self._commit()
        self.session.refresh(server)
        return FiveMServerResponse.model_validate(server)

    def update(self, server_id: int, payload: FiveMServerUpdate) -> FiveMServerResponse:
        server = self.get_model(server_id)
        values = payload.model_dump(exclude_unset=True, mode="python")
        for field, value in values.items():
            setattr(server, field, value)
        if values:
            server.updated_at = utc_now()
            self._commit()
        return FiveMServerResponse.model_validate(self.get_model(server_id))

    def mark_joined(self, server_id: int) -> FiveMServerResponse:
        server = self.get_model(server_id)
        server.last_joined_at = utc_now()
        server.updated_at = server.last_joined_at
        self.session.commit()
        return FiveMServerResponse.model_validate(server)

    def delete(self, server_id: int) -> None:
        self.session.delete(self.get_model(server_id))
        self.session.commit()

    def _commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise FiveMServerConflictError("That FiveM server address is already saved.") from exc

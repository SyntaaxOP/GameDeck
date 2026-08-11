"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.exc import OperationalError

from gamedeck import __version__
from gamedeck.api.games import router as games_router
from gamedeck.api.detections import router as detections_router
from gamedeck.api.fivem import router as fivem_router
from gamedeck.api.game_nights import router as game_nights_router
from gamedeck.api.steam import router as steam_router
from gamedeck.api.pc import router as pc_router
from gamedeck.api.analytics import router as analytics_router
from gamedeck.api.sessions import router as sessions_router
from gamedeck.api.purchases import router as purchases_router
from gamedeck.api.settings import router as settings_router
from gamedeck.api.tracker import router as tracker_router
from gamedeck.api.system import router as system_router
from gamedeck.config import AppSettings, get_settings
from gamedeck.db import Database
from gamedeck.domain.errors import DomainError
from gamedeck.logging_config import configure_logging
from gamedeck.monitoring.monitor import ProcessMonitor
from gamedeck.monitoring.process_source import ProcessSource, PsutilProcessSource
from gamedeck.models.game import Game
from gamedeck.services.artwork import ArtworkService
from gamedeck.services.steam import SteamService


logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    database: str
    version: str


def create_app(
    settings: AppSettings | None = None,
    *,
    enable_monitor: bool = True,
    process_source: ProcessSource | None = None,
) -> FastAPI:
    """Build an isolated application instance.

    Monitoring can be disabled or supplied with a fake process source in tests.
    """

    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level, app_settings.log_dir)
    database = Database(app_settings)
    monitor = ProcessMonitor(
        database,
        process_source or PsutilProcessSource(),
        app_settings=app_settings,
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.database = database
        logger.info("GameDeck backend starting", extra={"environment": app_settings.environment})
        if enable_monitor:
            try:
                with database.session_factory() as session:
                    result = SteamService(session, app_settings).sync_local_library()
                    if result.discovered:
                        logger.info(
                            "Local Steam library synchronized",
                            extra={
                                "discovered": result.discovered,
                                "imported": len(result.imported_game_ids),
                                "updated": len(result.updated_game_ids),
                            },
                        )
                    games = list(session.scalars(select(Game).where(Game.archived_at.is_(None))))
                    populated = ArtworkService(session, app_settings).populate_missing(games)
                    if populated:
                        logger.info("Game artwork cached", extra={"populated": len(populated)})
            except OSError:
                logger.warning("Local Steam discovery failed", exc_info=True)
        if enable_monitor:
            await monitor.start()
        try:
            yield
        finally:
            if enable_monitor:
                await monitor.stop()
            database.dispose()
            logger.info("GameDeck backend stopped")

    application = FastAPI(
        title=app_settings.app_name,
        version=__version__,
        lifespan=lifespan,
    )
    application.state.database = database
    application.state.monitor = monitor
    application.state.settings = app_settings
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://tauri.localhost", "https://tauri.localhost", "tauri://localhost"],
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    application.include_router(games_router)
    application.include_router(detections_router)
    application.include_router(fivem_router)
    application.include_router(game_nights_router)
    application.include_router(steam_router)
    application.include_router(pc_router)
    application.include_router(analytics_router)
    application.include_router(sessions_router)
    application.include_router(purchases_router)
    application.include_router(settings_router)
    application.include_router(tracker_router)
    application.include_router(system_router)

    @application.exception_handler(DomainError)
    async def handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": None}},
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "type": error["type"],
                "location": [str(part) for part in error["loc"]],
                "message": error["msg"],
                "input": error.get("input"),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "The request contains invalid fields.",
                    "details": details,
                }
            },
        )

    @application.exception_handler(SQLAlchemyError)
    async def handle_database_error(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
        message = str(getattr(exc, "orig", exc)).lower()
        busy = isinstance(exc, OperationalError) and (
            "database is locked" in message or "database is busy" in message
        )
        logger.exception("Database operation failed", extra={"database_busy": busy})
        if busy:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                headers={"Retry-After": "1"},
                content={"error": {
                    "code": "database_busy",
                    "message": "GameDeck is briefly busy. Wait a moment and try again.",
                    "details": None,
                }},
            )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {
                "code": "database_error",
                "message": "GameDeck could not complete the database operation.",
                "details": None,
            }},
        )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    def health(request: Request) -> HealthResponse:
        try:
            request.app.state.database.is_ready()
        except SQLAlchemyError as exc:
            logger.exception("Database readiness check failed")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "database_unavailable", "message": "Database is unavailable."},
            ) from exc
        return HealthResponse(status="healthy", database="ready", version=__version__)

    return application


app = create_app()

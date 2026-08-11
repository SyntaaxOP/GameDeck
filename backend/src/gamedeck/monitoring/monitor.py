"""Recovery-safe process monitor."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import threading
import time
from typing import Callable
from pathlib import Path, PureWindowsPath

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from gamedeck.db import Database
from gamedeck.config import AppSettings
from gamedeck.domain.errors import ExecutableConflictError
from gamedeck.integrations.steam_local import SteamDiscovery, discover_installed_games
from gamedeck.models.game import Game
from gamedeck.models.ignored_executable import IgnoredExecutable
from gamedeck.monitoring.game_candidate import (
    candidate_title,
    is_probable_game_candidate,
    normalize_executable_path,
)
from gamedeck.monitoring.matcher import match_games
from gamedeck.monitoring.process_source import ProcessInfo, ProcessSnapshotError, ProcessSource
from gamedeck.repositories.sessions import SessionRepository
from gamedeck.schemas.session import EndReason
from gamedeck.schemas.game import GameCreate
from gamedeck.schemas.settings import TrackerStatusResponse
from gamedeck.services.sessions import SessionService
from gamedeck.services.settings import SettingsService
from gamedeck.services.games import GameService
from gamedeck.services.artwork import ArtworkService
from gamedeck.services.steam import SteamService
from gamedeck.services.detections import AUTO_NOTE


logger = logging.getLogger(__name__)
HEARTBEAT_SECONDS = 15.0
UNKNOWN_GAME_CONFIRM_SECONDS = 15.0
STEAM_RESCAN_COOLDOWN_SECONDS = 30.0


@dataclass
class _Status:
    running: bool = False
    enabled: bool = True
    last_successful_scan_at: datetime | None = None
    last_error: str | None = None
    active_game_ids: tuple[int, ...] = ()
    scan_interval_seconds: int = 5
    restart_grace_seconds: int = 15


class ProcessMonitor:
    def __init__(
        self,
        database: Database,
        process_source: ProcessSource,
        *,
        utc_clock: Callable[[], datetime] | None = None,
        app_settings: AppSettings | None = None,
        steam_discovery: Callable[[Path | None], SteamDiscovery] = discover_installed_games,
        populate_artwork: bool = True,
    ) -> None:
        self.database = database
        self.process_source = process_source
        self.utc_clock = utc_clock or (lambda: datetime.now(UTC))
        self.app_settings = app_settings or AppSettings()
        self.steam_discovery = steam_discovery
        self.populate_artwork = populate_artwork
        self._initialized = False
        self._observed: set[int] = set()
        self._missing_since: dict[int, float] = {}
        self._last_heartbeat: dict[int, float] = {}
        self._candidate_first_seen: dict[str, float] = {}
        self._last_steam_rescan = float("-inf")
        self._status = _Status()
        self._status_lock = threading.Lock()
        self._stop = asyncio.Event()
        self._wake = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._loop_ref: asyncio.AbstractEventLoop | None = None

    async def start(self) -> None:
        if self._task is not None:
            return
        self._loop_ref = asyncio.get_running_loop()
        self._stop.clear()
        with self._status_lock:
            self._status.running = True
        self._task = asyncio.create_task(self._run(), name="gamedeck-process-monitor")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop.set()
        self._wake.set()
        await self._task
        await asyncio.to_thread(self.final_reconcile)
        self._task = None
        with self._status_lock:
            self._status.running = False

    def wake(self) -> None:
        if self._loop_ref and self._loop_ref.is_running():
            self._loop_ref.call_soon_threadsafe(self._wake.set)

    def configuration_changed(
        self, *, enabled: bool, scan_interval_seconds: int, restart_grace_seconds: int
    ) -> None:
        """Publish saved configuration immediately; the worker applies it on wake."""
        with self._status_lock:
            self._status.enabled = enabled
            self._status.scan_interval_seconds = scan_interval_seconds
            self._status.restart_grace_seconds = restart_grace_seconds
        self.wake()

    async def _run(self) -> None:
        while not self._stop.is_set():
            interval = await asyncio.to_thread(self.scan_once)
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=interval)
            except TimeoutError:
                pass
            self._wake.clear()

    def scan_once(self, monotonic_now: float | None = None) -> int:
        tick = time.monotonic() if monotonic_now is None else monotonic_now
        with self.database.session_factory() as session:
            settings = SettingsService(session).get_model()
            self._apply_config(settings)
            if not settings.tracking_enabled:
                self._initialized = False
                self._observed.clear()
                self._missing_since.clear()
                self._last_heartbeat.clear()
                self._candidate_first_seen.clear()
                with self._status_lock:
                    self._status.active_game_ids = ()
                return settings.scan_interval_seconds
            try:
                processes = self.process_source.snapshot()
            except (ProcessSnapshotError, OSError) as exc:
                self._record_error(exc)
                return settings.scan_interval_seconds

            observed_at = self._aware_now()
            games = list(session.scalars(select(Game).options(selectinload(Game.executable_mappings)).where(Game.archived_at.is_(None))))
            if self._sync_unknown_steam_processes(session, games, processes, tick):
                games = self._load_games(session)
            matches = match_games(games, processes)
            if self._promote_foreground_candidate(session, games, processes, matches, tick, observed_at):
                games = self._load_games(session)
                matches = match_games(games, processes)
            service = SessionService(session)

            if not self._initialized:
                active = {item.game_id: item for item in SessionRepository(session).list_active()}
                for game_id in active.keys() - matches.keys():
                    service.end_active_session(game_id, reason=EndReason.RECOVERED)
                for game_id, matched in matches.items():
                    self._touch(service, game_id, matched, observed_at)
                    self._last_heartbeat[game_id] = tick
                self._initialized = True
                self._observed = set(matches)
            else:
                self._reconcile(service, matches, observed_at, tick, settings.restart_grace_seconds)

            self._record_success(observed_at, matches)
            return settings.scan_interval_seconds

    @staticmethod
    def _load_games(session: Session) -> list[Game]:
        return list(session.scalars(
            select(Game).options(selectinload(Game.executable_mappings)).where(Game.archived_at.is_(None))
        ))

    def _sync_unknown_steam_processes(
        self,
        session: Session,
        games: list[Game],
        processes: list[ProcessInfo],
        tick: float,
    ) -> bool:
        if tick - self._last_steam_rescan < STEAM_RESCAN_COOLDOWN_SECONDS:
            return False
        matched_pids = {process.pid for items in match_games(games, processes).values() for process in items}
        unknown = [
            process for process in processes
            if process.pid not in matched_pids
            and process.executable_path
            and "\\steamapps\\common\\" in normalize_executable_path(process.executable_path)
        ]
        if not unknown:
            return False
        self._last_steam_rescan = tick
        discovery = self.steam_discovery(self.app_settings.steam_path)
        result = SteamService(
            session, self.app_settings, discovery=discovery
        ).sync_local_library()
        changed = bool(result.imported_game_ids or result.updated_game_ids)
        if changed:
            if self.populate_artwork:
                changed_ids = [*result.imported_game_ids, *result.updated_game_ids]
                changed_games = [game for game_id in changed_ids if (game := session.get(Game, game_id))]
                ArtworkService(session, self.app_settings).populate_missing(changed_games)
            logger.info(
                "Running Steam game discovered on demand",
                extra={"imported": len(result.imported_game_ids), "updated": len(result.updated_game_ids)},
            )
        return changed

    def _promote_foreground_candidate(
        self,
        session: Session,
        games: list[Game],
        processes: list[ProcessInfo],
        matches: dict[int, list[ProcessInfo]],
        tick: float,
        observed_at: datetime,
    ) -> bool:
        matched_pids = {process.pid for items in matches.values() for process in items}
        ignored = list(session.scalars(select(IgnoredExecutable)))
        candidates = [
            process for process in processes
            if process.pid not in matched_pids
            and is_probable_game_candidate(process)
            and not self._is_ignored(process, ignored)
        ]
        active_paths = {
            normalize_executable_path(process.executable_path)
            for process in candidates
            if process.executable_path
        }
        self._candidate_first_seen = {
            path: first_seen
            for path, first_seen in self._candidate_first_seen.items()
            if path in active_paths
        }
        for process in candidates:
            path = normalize_executable_path(process.executable_path or "")
            first_seen = self._candidate_first_seen.setdefault(path, tick)
            if tick - first_seen < UNKNOWN_GAME_CONFIRM_SECONDS:
                continue
            try:
                game = GameService(session).create(GameCreate(
                    title=candidate_title(process),
                    platform="local",
                    executable_name=PureWindowsPath(path).name,
                    executable_path=process.executable_path,
                    install_directory=str(PureWindowsPath(process.executable_path or "").parent),
                    discovered_at=observed_at.replace(tzinfo=None),
                    notes=AUTO_NOTE,
                ))
                if self.populate_artwork:
                    ArtworkService(session, self.app_settings).populate_missing([game])
            except ExecutableConflictError:
                self._candidate_first_seen.pop(path, None)
                continue
            self._candidate_first_seen.pop(path, None)
            logger.info("Unlisted game detected", extra={"game_id": game.id, "executable": path})
            return True
        return False

    @staticmethod
    def _is_ignored(process: ProcessInfo, ignored: list[IgnoredExecutable]) -> bool:
        path = normalize_executable_path(process.executable_path or "")
        name = process.executable_name.casefold()
        return any(
            (item.executable_path and item.executable_path == path)
            or (not item.executable_path and item.executable_name == name)
            for item in ignored
        )

    def _reconcile(
        self,
        service: SessionService,
        matches: dict[int, list[ProcessInfo]],
        observed_at: datetime,
        tick: float,
        grace_seconds: int,
    ) -> None:
        running = set(matches)
        for game_id, matched in matches.items():
            reappeared = game_id in self._missing_since
            self._missing_since.pop(game_id, None)
            if (
                game_id not in self._observed
                or reappeared
                or tick - self._last_heartbeat.get(game_id, float("-inf")) >= HEARTBEAT_SECONDS
            ):
                self._touch(service, game_id, matched, observed_at)
                self._last_heartbeat[game_id] = tick
            self._observed.add(game_id)

        for game_id in list(self._observed - running):
            missing_at = self._missing_since.setdefault(game_id, tick)
            if tick - missing_at >= grace_seconds:
                service.end_active_session(game_id, reason=EndReason.PROCESS_STOPPED)
                self._observed.discard(game_id)
                self._missing_since.pop(game_id, None)
                self._last_heartbeat.pop(game_id, None)

    def final_reconcile(self) -> None:
        if not self._initialized:
            return
        with self.database.session_factory() as session:
            settings = SettingsService(session).get_model()
            if not settings.tracking_enabled:
                return
            try:
                processes = self.process_source.snapshot()
            except (ProcessSnapshotError, OSError) as exc:
                self._record_error(exc)
                return
            now = self._aware_now()
            games = list(session.scalars(select(Game).options(selectinload(Game.executable_mappings)).where(Game.archived_at.is_(None))))
            matches = match_games(games, processes)
            service = SessionService(session)
            active_ids = {item.game_id for item in SessionRepository(session).list_active()}
            for game_id, matched in matches.items():
                self._touch(service, game_id, matched, now)
            for game_id in active_ids - matches.keys():
                service.end_active_session(game_id, reason=EndReason.TRACKER_SHUTDOWN)
            self._record_success(now, matches)

    def status(self) -> TrackerStatusResponse:
        with self._status_lock:
            current = _Status(**vars(self._status))
        return TrackerStatusResponse(
            running=current.running,
            enabled=current.enabled,
            last_successful_scan_at=current.last_successful_scan_at,
            last_error=current.last_error,
            active_game_ids=list(current.active_game_ids),
            scan_interval_seconds=current.scan_interval_seconds,
            restart_grace_seconds=current.restart_grace_seconds,
        )

    @staticmethod
    def _touch(
        service: SessionService,
        game_id: int,
        processes: list[ProcessInfo],
        observed_at: datetime,
    ) -> None:
        process = min(processes, key=lambda item: item.created_at or observed_at)
        service.start_process_session(
            game_id,
            observed_at=observed_at,
            process_id=process.pid,
            process_started_at=process.created_at,
        )

    def _apply_config(self, settings: object) -> None:
        with self._status_lock:
            self._status.enabled = bool(settings.tracking_enabled)
            self._status.scan_interval_seconds = int(settings.scan_interval_seconds)
            self._status.restart_grace_seconds = int(settings.restart_grace_seconds)

    def _record_success(self, at: datetime, matches: dict[int, list[ProcessInfo]]) -> None:
        with self._status_lock:
            self._status.last_successful_scan_at = at
            self._status.last_error = None
            self._status.active_game_ids = tuple(sorted(matches))

    def _record_error(self, exc: Exception) -> None:
        logger.warning("Process scan failed", exc_info=exc)
        with self._status_lock:
            self._status.last_error = str(exc) or exc.__class__.__name__

    def _aware_now(self) -> datetime:
        value = self.utc_clock()
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

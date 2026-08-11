"""Steam owned-library import and automatic local installation discovery."""

from datetime import UTC, datetime
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from gamedeck.config import AppSettings
from gamedeck.domain.errors import SteamConfigurationError, SteamUnavailableError
from gamedeck.integrations.steam_local import SteamDiscovery, discover_installed_games
from gamedeck.models.game import Game
from gamedeck.schemas.game import GameCreate
from gamedeck.schemas.steam import (
    SteamConfigurationResponse,
    SteamGamePreview,
    SteamImportRequest,
    SteamImportResponse,
    SteamInstalledGame,
    SteamLocalLibraryResponse,
    SteamLocalSyncResponse,
    SteamPreviewResponse,
)
from gamedeck.services.games import GameService


class SteamClient:
    endpoint = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"

    def fetch_owned(self, key: str, steam_id: str) -> list[dict[str, object]]:
        query = urlencode({
            "key": key,
            "steamid": steam_id,
            "include_appinfo": "true",
            "include_played_free_games": "true",
            "format": "json",
        })
        request = Request(f"{self.endpoint}?{query}", headers={"User-Agent": "GameDeck/0.8"})
        try:
            with urlopen(request, timeout=10) as response:
                payload = json.load(response)
        except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise SteamUnavailableError(
                "Steam library data is unavailable. Existing GameDeck data is unchanged."
            ) from exc
        return list(payload.get("response", {}).get("games", []))


class SteamService:
    def __init__(
        self,
        session: Session,
        settings: AppSettings,
        client: SteamClient | None = None,
        *,
        discovery: SteamDiscovery | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.client = client or SteamClient()
        self._discovery = discovery

    def configuration(self) -> SteamConfigurationResponse:
        return SteamConfigurationResponse(
            configured=self.settings.steam_api_key is not None and self.settings.steam_id is not None,
            steam_id=self.settings.steam_id,
        )

    def local_library(self) -> SteamLocalLibraryResponse:
        discovery = self._discover()
        existing = {
            game.steam_app_id: game
            for game in self.session.scalars(
                select(Game).where(Game.steam_app_id.is_not(None))
            )
        }
        games = [
            SteamInstalledGame(
                app_id=item.app_id,
                name=item.name,
                install_directory=str(item.install_directory),
                already_imported=item.app_id in existing,
            )
            for item in discovery.games
        ]
        return SteamLocalLibraryResponse(
            steam_path=str(discovery.steam_path) if discovery.steam_path else None,
            library_paths=[str(path) for path in discovery.library_paths],
            games=games,
            total=len(games),
        )

    def sync_local_library(self) -> SteamLocalSyncResponse:
        discovery = self._discover()
        existing = {
            game.steam_app_id: game
            for game in self.session.scalars(
                select(Game).where(Game.steam_app_id.is_not(None))
            )
        }
        imported: list[int] = []
        updated: list[int] = []
        now = datetime.now(UTC).replace(tzinfo=None)

        for item in discovery.games:
            game = existing.get(item.app_id)
            if game is None:
                game = GameService(self.session).create(GameCreate(
                    title=item.name,
                    platform="steam",
                    executable_name=f"steam-app-{item.app_id}.exe",
                    steam_app_id=item.app_id,
                    install_directory=str(item.install_directory),
                    discovered_at=now,
                    notes="Discovered from the locally installed Steam library.",
                ))
                existing[item.app_id] = game
                imported.append(game.id)
                continue

            changed = False
            install_directory = str(item.install_directory)
            if game.install_directory != install_directory:
                game.install_directory = install_directory
                changed = True
            game.discovered_at = now
            if changed:
                game.updated_at = now
                updated.append(game.id)

        self.session.commit()
        return SteamLocalSyncResponse(
            discovered=len(discovery.games),
            imported_game_ids=imported,
            updated_game_ids=updated,
        )

    def preview(self, steam_id: str | None) -> SteamPreviewResponse:
        key = self.settings.steam_api_key.get_secret_value() if self.settings.steam_api_key else None
        resolved = steam_id or self.settings.steam_id
        if not key or not resolved:
            raise SteamConfigurationError(
                "Set GAMEDECK_STEAM_API_KEY and GAMEDECK_STEAM_ID before importing."
            )
        existing = set(self.session.scalars(
            select(Game.steam_app_id).where(Game.steam_app_id.is_not(None))
        ))
        games = [
            SteamGamePreview(
                app_id=int(item["appid"]),
                name=str(item.get("name") or f"Steam app {item['appid']}"),
                playtime_minutes=int(item.get("playtime_forever", 0)),
                already_imported=int(item["appid"]) in existing,
            )
            for item in self.client.fetch_owned(key, resolved)
        ]
        games.sort(key=lambda item: (item.already_imported, item.name.casefold()))
        return SteamPreviewResponse(steam_id=resolved, games=games, total=len(games))

    def import_games(self, payload: SteamImportRequest) -> SteamImportResponse:
        existing = set(self.session.scalars(
            select(Game.steam_app_id).where(Game.steam_app_id.is_not(None))
        ))
        imported: list[int] = []
        skipped: list[int] = []
        for item in payload.items:
            if item.app_id in existing:
                skipped.append(item.app_id)
                continue
            game = GameService(self.session).create(GameCreate(
                title=item.name,
                platform="steam",
                executable_name=f"steam-app-{item.app_id}.exe",
                steam_app_id=item.app_id,
                notes="Imported from Steam. Install locally to enable automatic process tracking.",
            ))
            imported.append(game.id)
            existing.add(item.app_id)
        return SteamImportResponse(imported_game_ids=imported, skipped_app_ids=skipped)

    def _discover(self) -> SteamDiscovery:
        if self._discovery is None:
            self._discovery = discover_installed_games(self.settings.steam_path)
        return self._discovery

"""Locally cached game artwork from trusted sources and executable resources."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
import json
import logging
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError

from sqlalchemy.orm import Session

from gamedeck.config import AppSettings
from gamedeck.integrations.windows_icon import extract_executable_icon
from gamedeck.integrations.steam_local import find_steam_path
from gamedeck.models.game import Game


logger = logging.getLogger(__name__)
MAX_ARTWORK_BYTES = 10 * 1024 * 1024
STEAM_HEADER_URL = (
    "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{app_id}/header.jpg"
)
Downloader = Callable[[int, Path], bool]
TitleDownloader = Callable[[str, Path], bool]
SteamBannerBuilder = Callable[[int, Path | None, Path], bool]
IconExtractor = Callable[[Path, Path], bool]
IGNORED_ICON_EXECUTABLE_PREFIXES = (
    "crash",
    "dxsetup",
    "easyanticheat",
    "install",
    "launcher",
    "setup",
    "unins",
    "uninstall",
    "vc_redist",
)
MANAGED_ARTWORK_PREFIXES = ("steam-", "game-", "wikipedia-")
STEAM_CACHE_NAMES = {
    "library_header.jpg": 0,
    "library_header.png": 0,
    "header.jpg": 1,
    "header.png": 1,
    "library_hero.jpg": 2,
    "library_hero.png": 2,
    "library_capsule.jpg": 3,
    "library_600x900.jpg": 3,
}


def download_steam_header(app_id: int, destination: Path) -> bool:
    request = Request(
        STEAM_HEADER_URL.format(app_id=app_id),
        headers={"User-Agent": "GameDeck/0.8 artwork cache"},
    )
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urlopen(request, timeout=8) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"image/jpeg", "image/png"}:
                return False
            payload = response.read(MAX_ARTWORK_BYTES + 1)
        if len(payload) > MAX_ARTWORK_BYTES or not (
            payload.startswith(b"\xff\xd8\xff") or payload.startswith(b"\x89PNG\r\n\x1a\n")
        ):
            return False
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_bytes(payload)
        temporary.replace(destination)
        return True
    except (HTTPError, URLError, TimeoutError, OSError):
        temporary.unlink(missing_ok=True)
        return False


def find_cached_steam_artwork(app_id: int, configured_path: Path | None) -> Path | None:
    steam_path = find_steam_path(configured_path)
    if steam_path is None:
        return None
    cache = steam_path / "appcache" / "librarycache" / str(app_id)
    if not cache.is_dir():
        return None
    candidates: list[tuple[int, int, Path]] = []
    try:
        for image in cache.rglob("*"):
            if not image.is_file() or "blur" in image.name.casefold():
                continue
            priority = STEAM_CACHE_NAMES.get(image.name.casefold())
            if priority is None:
                continue
            try:
                candidates.append((priority, -image.stat().st_size, image))
            except OSError:
                continue
    except OSError:
        return None
    return min(candidates, default=(99, 0, None), key=lambda item: (item[0], item[1]))[2]


def build_cached_steam_banner(
    app_id: int, configured_path: Path | None, destination: Path
) -> bool:
    """Compose Steam's full-resolution hero and transparent logo for a sharp card banner."""
    steam_path = find_steam_path(configured_path)
    if steam_path is None:
        return False
    cache = steam_path / "appcache" / "librarycache" / str(app_id)
    if not cache.is_dir():
        return False
    try:
        heroes = [
            path for path in cache.rglob("library_hero.*")
            if path.is_file()
            and "blur" not in path.name.casefold()
            and path.suffix.casefold() in {".jpg", ".jpeg", ".png"}
        ]
        logos = [
            path for path in cache.rglob("logo.png") if path.is_file()
        ]
        hero = max(heroes, key=lambda path: path.stat().st_size, default=None)
        if hero is None:
            return False
        logo = max(logos, key=lambda path: path.stat().st_size, default=None)
        with Image.open(hero) as source:
            banner = ImageOps.fit(
                source.convert("RGB"),
                (1280, 560),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            ).convert("RGBA")
        if logo is not None:
            with Image.open(logo) as logo_source:
                mark = logo_source.convert("RGBA")
                alpha_box = mark.getchannel("A").getbbox()
                if alpha_box:
                    mark = mark.crop(alpha_box)
                mark.thumbnail((700, 330), Image.Resampling.LANCZOS)
            position = ((banner.width - mark.width) // 2, (banner.height - mark.height) // 2)
            shadow = Image.new("RGBA", banner.size)
            shadow_mark = Image.new("RGBA", mark.size, (0, 0, 0, 0))
            shadow_mark.putalpha(mark.getchannel("A").filter(ImageFilter.GaussianBlur(10)))
            shadow.alpha_composite(shadow_mark, (position[0] + 5, position[1] + 7))
            banner = Image.alpha_composite(banner, shadow)
            banner.alpha_composite(mark, position)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".part")
        banner.convert("RGB").save(temporary, format="JPEG", quality=94, optimize=True)
        temporary.replace(destination)
        return True
    except (OSError, UnidentifiedImageError):
        return False


def download_wikipedia_cover(title: str, destination: Path) -> bool:
    """Resolve a confidently matched video-game page image via Wikimedia's documented API."""
    search_query = urlencode({"q": f'"{title}" video game', "limit": 5})
    search = _read_json(f"https://en.wikipedia.org/w/rest.php/v1/search/page?{search_query}")
    if not search:
        return False
    expected = _normalized_title(title)
    pages = search.get("pages", [])
    match = next((
        page for page in pages
        if _normalized_title(str(page.get("title", ""))) == expected
        and "video game" in str(page.get("description", "")).casefold()
    ), None)
    if match is None:
        return False
    image_query = urlencode({
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "prop": "pageimages",
        "titles": str(match["title"]),
        "piprop": "thumbnail",
        "pithumbsize": 1200,
        "pilicense": "any",
        "redirects": 1,
    })
    details = _read_json(f"https://en.wikipedia.org/w/api.php?{image_query}")
    try:
        image_url = str(details["query"]["pages"][0]["thumbnail"]["source"])
    except (KeyError, IndexError, TypeError):
        return False
    if urlparse(image_url).hostname not in {"upload.wikimedia.org"}:
        return False
    return _download_normalized_image(image_url, destination)


def _read_json(url: str) -> dict[str, object] | None:
    request = Request(url, headers={"User-Agent": "GameDeck/0.8 (local personal game library)"})
    try:
        with urlopen(request, timeout=8) as response:
            payload = response.read(MAX_ARTWORK_BYTES + 1)
        if len(payload) > MAX_ARTWORK_BYTES:
            return None
        value = json.loads(payload)
        return value if isinstance(value, dict) else None
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError):
        return None


def _download_normalized_image(url: str, destination: Path) -> bool:
    request = Request(url, headers={"User-Agent": "GameDeck/0.8 (local personal game library)"})
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urlopen(request, timeout=8) as response:
            payload = response.read(MAX_ARTWORK_BYTES + 1)
        if len(payload) > MAX_ARTWORK_BYTES:
            return False
        with Image.open(BytesIO(payload)) as source:
            source.load()
            if source.width < 200 or source.height < 200:
                return False
            image = source.convert("RGB")
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            destination.parent.mkdir(parents=True, exist_ok=True)
            image.save(temporary, format="JPEG", quality=92, optimize=True)
        temporary.replace(destination)
        return True
    except (HTTPError, URLError, TimeoutError, OSError, UnidentifiedImageError):
        temporary.unlink(missing_ok=True)
        return False


def _normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


class ArtworkService:
    def __init__(
        self,
        session: Session,
        settings: AppSettings,
        *,
        steam_downloader: Downloader = download_steam_header,
        steam_banner_builder: SteamBannerBuilder = build_cached_steam_banner,
        title_downloader: TitleDownloader = download_wikipedia_cover,
        icon_extractor: IconExtractor = extract_executable_icon,
    ) -> None:
        self.session = session
        self.settings = settings
        self.steam_downloader = steam_downloader
        self.steam_banner_builder = steam_banner_builder
        self.title_downloader = title_downloader
        self.icon_extractor = icon_extractor

    def populate_missing(self, games: list[Game]) -> list[int]:
        populated: list[int] = []
        for game in games:
            if self.populate_game(game):
                populated.append(game.id)
        if populated:
            self.session.commit()
        return populated

    def populate_game(self, game: Game) -> bool:
        existing = Path(game.cover_path) if game.cover_path else None
        managed = existing is not None and existing.name.startswith(MANAGED_ARTWORK_PREFIXES)
        if existing is not None and not managed:
            return False
        destination: Path | None = None
        created = False
        try:
            if game.steam_app_id:
                destination = self.settings.artwork_dir / f"steam-{game.steam_app_id}-library-banner.jpg"
                if destination.is_file() or self.steam_banner_builder(
                    game.steam_app_id, self.settings.steam_path, destination
                ):
                    created = True
                elif existing is not None and existing.is_file():
                    return False
                else:
                    destination = self.settings.artwork_dir / f"steam-{game.steam_app_id}-header.jpg"
                    created = destination.is_file() or self.steam_downloader(game.steam_app_id, destination)
            elif existing is not None and existing.is_file() and existing.name.startswith("wikipedia-"):
                return False
            if not created:
                destination = self.settings.artwork_dir / f"wikipedia-{game.id}-cover.jpg"
                created = destination.is_file() or self.title_downloader(game.title, destination)
            if not created:
                if existing is not None and existing.is_file():
                    return False
                executable = self._icon_executable(game)
                if executable is None:
                    return False
                destination = self.settings.artwork_dir / f"game-{game.id}-icon.png"
                created = destination.is_file() or self.icon_extractor(
                    executable, destination
                )
        except OSError:
            logger.warning("Game artwork extraction failed", exc_info=True, extra={"game_id": game.id})
            return False
        if not created or destination is None:
            return False
        game.cover_path = str(destination.resolve())
        return True

    @staticmethod
    def _icon_executable(game: Game) -> Path | None:
        if game.executable_path:
            executable = Path(game.executable_path)
            if executable.is_file():
                return executable
        if not game.install_directory:
            return None
        root = Path(game.install_directory)
        if not root.is_dir():
            return None
        candidates: list[tuple[int, Path]] = []
        try:
            for executable in root.rglob("*.exe"):
                name = executable.name.casefold()
                if name.startswith(IGNORED_ICON_EXECUTABLE_PREFIXES):
                    continue
                try:
                    candidates.append((executable.stat().st_size, executable))
                except OSError:
                    continue
        except OSError:
            return None
        return max(candidates, default=(0, None), key=lambda item: item[0])[1]

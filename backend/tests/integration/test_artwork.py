from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from gamedeck.config import AppSettings
from gamedeck.schemas.game import GameCreate
from gamedeck.services.artwork import ArtworkService
from gamedeck.services import artwork as artwork_module
from gamedeck.services.games import GameService


def test_steam_artwork_is_cached_and_assigned_without_overwriting(db_session, tmp_path: Path) -> None:
    game = GameService(db_session).create(GameCreate(
        title="Hades",
        platform="steam",
        executable_name="steam-app-1145360.exe",
        steam_app_id=1145360,
    ))
    calls: list[int] = []

    def download(app_id: int, destination: Path) -> bool:
        calls.append(app_id)
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"\xff\xd8\xfftest")
        return True

    settings = AppSettings(artwork_dir=tmp_path / "artwork")
    service = ArtworkService(
        db_session,
        settings,
        steam_downloader=download,
        steam_banner_builder=lambda _app_id, _path, _destination: False,
    )

    assert service.populate_missing([game]) == [game.id]
    assert calls == [1145360]
    assert Path(game.cover_path or "").read_bytes() == b"\xff\xd8\xfftest"
    assert service.populate_missing([game]) == []
    assert calls == [1145360]


def test_local_executable_icon_is_cached(db_session, tmp_path: Path) -> None:
    executable = tmp_path / "MoonGame.exe"
    executable.touch()
    game = GameService(db_session).create(GameCreate(
        title="Moon Game",
        platform="local",
        executable_name="moongame.exe",
        executable_path=str(executable),
    ))

    def extract(source: Path, destination: Path) -> bool:
        assert source == executable
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"\x89PNG\r\n\x1a\nicon")
        return True

    service = ArtworkService(
        db_session,
        AppSettings(artwork_dir=tmp_path / "artwork"),
        title_downloader=lambda _title, _destination: False,
        icon_extractor=extract,
    )

    assert service.populate_missing([game]) == [game.id]
    assert Path(game.cover_path or "").suffix == ".png"


def test_steam_game_falls_back_to_largest_install_executable_icon(
    db_session, tmp_path: Path
) -> None:
    install = tmp_path / "SteamLibrary" / "steamapps" / "common" / "NoStoreArt"
    install.mkdir(parents=True)
    (install / "launcher.exe").write_bytes(b"small")
    main_executable = install / "NoStoreArt-Win64-Shipping.exe"
    main_executable.write_bytes(b"main executable")
    game = GameService(db_session).create(GameCreate(
        title="No Store Art",
        platform="steam",
        executable_name="steam-app-999002.exe",
        steam_app_id=999002,
        install_directory=str(install),
    ))
    extracted: list[Path] = []

    def extract(source: Path, destination: Path) -> bool:
        extracted.append(source)
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"\x89PNG\r\n\x1a\nicon")
        return True

    service = ArtworkService(
        db_session,
        AppSettings(artwork_dir=tmp_path / "artwork"),
        steam_downloader=lambda _app_id, _destination: False,
        steam_banner_builder=lambda _app_id, _path, _destination: False,
        title_downloader=lambda _title, _destination: False,
        icon_extractor=extract,
    )

    assert service.populate_missing([game]) == [game.id]
    assert extracted == [main_executable]
    assert Path(game.cover_path or "").suffix == ".png"


def test_local_steam_header_upgrades_managed_icon_without_overwriting_manual_cover(
    db_session, tmp_path: Path
) -> None:
    cached = b"high resolution branded steam banner"
    managed_icon = tmp_path / "artwork" / "game-20-icon.png"
    managed_icon.parent.mkdir()
    managed_icon.write_bytes(b"icon")
    game = GameService(db_session).create(GameCreate(
        title="Cached Game",
        platform="steam",
        executable_name="steam-app-880001.exe",
        steam_app_id=880001,
        cover_path=str(managed_icon),
    ))
    service = ArtworkService(
        db_session,
        AppSettings(artwork_dir=tmp_path / "artwork"),
        steam_banner_builder=lambda _app_id, _path, destination: (
            destination.write_bytes(cached) or True
        ),
    )

    assert service.populate_missing([game]) == [game.id]
    assert Path(game.cover_path or "").name == "steam-880001-library-banner.jpg"
    assert Path(game.cover_path or "").read_bytes() == cached

    manual = tmp_path / "my-custom-cover.jpg"
    manual.write_bytes(b"manual")
    game.cover_path = str(manual)
    db_session.commit()
    assert service.populate_missing([game]) == []
    assert game.cover_path == str(manual)


def test_cached_steam_hero_and_logo_create_large_branded_banner(tmp_path: Path) -> None:
    steam = tmp_path / "Steam"
    (steam / "steamapps").mkdir(parents=True)
    cache = steam / "appcache" / "librarycache" / "880002" / "hash"
    cache.mkdir(parents=True)
    Image.new("RGB", (1920, 620), "navy").save(cache / "library_hero.jpg")
    logo = Image.new("RGBA", (640, 360), (0, 0, 0, 0))
    ImageDraw.Draw(logo).rectangle((80, 100, 560, 260), fill="white")
    logo.save(cache / "logo.png")
    destination = tmp_path / "banner.jpg"

    assert artwork_module.build_cached_steam_banner(880002, steam, destination) is True
    with Image.open(destination) as banner:
        assert banner.size == (1280, 560)


def test_game_cover_endpoint_serves_only_assigned_image(api_client: TestClient, tmp_path: Path) -> None:
    artwork = tmp_path / "cover.png"
    artwork.write_bytes(b"\x89PNG\r\n\x1a\ncover")
    created = api_client.post("/api/v1/games", json={
        "title": "Cover Test",
        "platform": "local",
        "executable_name": "cover-test.exe",
        "cover_path": str(artwork),
    })
    assert created.status_code == 201

    response = api_client.get(f"/api/v1/games/{created.json()['id']}/cover")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == artwork.read_bytes()


def test_wikipedia_fallback_requires_exact_video_game_match(monkeypatch, tmp_path: Path) -> None:
    responses = iter([
        {"pages": [
            {"title": "Moon Game", "description": "2026 video game"},
            {"title": "Moon", "description": "natural satellite"},
        ]},
        {"query": {"pages": [{"thumbnail": {
            "source": "https://upload.wikimedia.org/example/moon-game.jpg"
        }}]}},
    ])
    monkeypatch.setattr(artwork_module, "_read_json", lambda _url: next(responses))
    downloaded: list[str] = []
    monkeypatch.setattr(
        artwork_module,
        "_download_normalized_image",
        lambda url, _destination: downloaded.append(url) or True,
    )

    assert artwork_module.download_wikipedia_cover("Moon Game", tmp_path / "cover.jpg") is True
    assert downloaded == ["https://upload.wikimedia.org/example/moon-game.jpg"]

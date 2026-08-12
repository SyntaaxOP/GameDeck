from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from gamedeck.config import AppSettings
from gamedeck.main import create_app
from gamedeck.models.game import Game
from gamedeck.models.game_executable import GameExecutable
from gamedeck.integrations.steam_local import SteamDiscovery, SteamInstall
from gamedeck.monitoring.game_candidate import candidate_title, is_probable_game_candidate
from gamedeck.monitoring.matcher import match_games
from gamedeck.monitoring.monitor import ProcessMonitor
from gamedeck.monitoring.process_source import ProcessInfo, ProcessSnapshotError
from gamedeck.monitoring.process_source import PsutilProcessSource
from gamedeck.repositories.sessions import SessionRepository
from gamedeck.schemas.game import GameCreate
from gamedeck.services.games import GameService


START = datetime(2026, 8, 11, 8, 0, tzinfo=UTC)


class FakeProcessSource:
    def __init__(self) -> None:
        self.processes: list[ProcessInfo] = []
        self.error: Exception | None = None

    def snapshot(self) -> list[ProcessInfo]:
        if self.error:
            raise self.error
        return self.processes


def test_process_source_skips_an_inaccessible_process(monkeypatch) -> None:
    import psutil

    class InaccessibleProcess:
        @property
        def info(self):
            raise psutil.AccessDenied(pid=44)

    monkeypatch.setattr(psutil, "process_iter", lambda _fields: [InaccessibleProcess()])
    assert PsutilProcessSource().snapshot() == []


def test_matcher_is_case_insensitive_path_aware_and_groups_processes() -> None:
    game = Game(id=1, title="Hades", platform="steam", executable_name="hades.exe",
                executable_path=r"C:\Games\Hades\hades.exe")
    right = ProcessInfo(1, "HADES.EXE", r"c:\games\hades\HADES.exe")
    duplicate = ProcessInfo(2, "hades.exe", r"C:\Games\Hades\hades.exe")
    wrong = ProcessInfo(3, "hades.exe", r"D:\Other\hades.exe")

    matches = match_games([game], [right, duplicate, wrong])

    assert matches[1] == [right, duplicate]
    assert match_games([game], [ProcessInfo(4, "hades.exe", None)])[1][0].pid == 4
    assert match_games([game], [wrong]) == {}


def test_matcher_combines_primary_and_alias_processes_for_one_game() -> None:
    game = Game(id=1, title="Hades", platform="steam", executable_name="hades.exe")
    game.executable_mappings = [
        GameExecutable(id=1, executable_name="hades.exe", is_primary=True, active=True),
        GameExecutable(id=2, executable_name="hades-launcher.exe", is_primary=False, active=True),
    ]
    primary = ProcessInfo(1, "hades.exe")
    alias = ProcessInfo(2, "HADES-LAUNCHER.EXE")

    assert match_games([game], [primary, alias]) == {1: [primary, alias]}


def test_matcher_recognizes_any_game_process_inside_discovered_steam_directory() -> None:
    game = Game(
        id=1,
        title="Hades",
        platform="steam",
        executable_name="steam-app-1145360.exe",
        install_directory=r"D:\SteamLibrary\steamapps\common\Hades",
    )
    game.executable_mappings = []
    game_process = ProcessInfo(
        50,
        "Hades-Win64-Shipping.exe",
        r"D:\SteamLibrary\steamapps\common\Hades\x64\Hades-Win64-Shipping.exe",
    )
    unrelated = ProcessInfo(51, "Hades.exe", r"D:\Downloads\Hades.exe")

    assert match_games([game], [game_process, unrelated]) == {1: [game_process]}


def test_generic_candidate_requires_foreground_and_excludes_browser() -> None:
    game = ProcessInfo(
        10,
        "starlight.exe",
        r"C:\Games\Starlight\starlight.exe",
        is_foreground=True,
        window_title="Starlight",
    )
    background = ProcessInfo(
        11,
        "another.exe",
        r"C:\Games\Another\another.exe",
        window_title="Another",
    )
    browser = ProcessInfo(
        12,
        "chrome.exe",
        r"C:\Program Files\Google\Chrome\chrome.exe",
        is_foreground=True,
        window_title="Game guide - Chrome",
    )
    assistant = ProcessInfo(
        13,
        "ChatGPT.exe",
        r"C:\Program Files\WindowsApps\OpenAI.Codex\app\ChatGPT.exe",
        is_foreground=True,
        window_title="Codex",
    )

    assert is_probable_game_candidate(game) is True
    assert candidate_title(game) == "Starlight"
    assert is_probable_game_candidate(background) is False
    assert is_probable_game_candidate(browser) is False
    assert is_probable_game_candidate(assistant) is False


def test_generic_candidate_rejects_screenshots_capture_tools_and_unrelated_apps() -> None:
    screenshot = ProcessInfo(
        pid=12,
        name="photos.exe",
        executable_path=r"C:\Program Files\WindowsApps\Microsoft.Windows.Photos\Photos.exe",
        is_foreground=True,
        window_title="Screenshot 2026-08-12 060311.png",
    )
    capture_tool = ProcessInfo(
        pid=13,
        name="Medal.exe",
        executable_path=r"C:\Users\player\AppData\Local\Medal\Medal.exe",
        is_foreground=True,
        window_title="Medal",
    )
    unrelated = ProcessInfo(
        pid=14,
        name="DrawingTool.exe",
        executable_path=r"C:\Tools\DrawingTool.exe",
        is_foreground=True,
        window_title="Drawing Tool",
    )
    gamedeck_sidecar = ProcessInfo(
        pid=15,
        name="gamedeck-api-x86_64-pc-windows-msvc.exe",
        executable_path=r"C:\Projects\GameDeck\src-tauri\binaries\gamedeck-api-x86_64-pc-windows-msvc.exe",
        is_foreground=True,
        window_title="Unhandled exception in script",
    )
    assert is_probable_game_candidate(screenshot) is False
    assert is_probable_game_candidate(capture_tool) is False
    assert is_probable_game_candidate(unrelated) is False
    assert is_probable_game_candidate(gamedeck_sidecar) is False


def test_monitor_auto_imports_sustained_unknown_foreground_game(
    migrated_database: tuple[Path, str], tmp_path: Path
) -> None:
    _, database_url = migrated_database
    settings = AppSettings(database_url=database_url, log_dir=tmp_path / "logs")
    app = create_app(settings, enable_monitor=False)
    database = app.state.database
    source = FakeProcessSource()
    source.processes = [ProcessInfo(
        410,
        "starlight.exe",
        r"C:\Games\Starlight\starlight.exe",
        created_at=START,
        is_foreground=True,
        window_title="Starlight",
    )]
    monitor = ProcessMonitor(
        database, source, utc_clock=lambda: START, app_settings=settings, populate_artwork=False
    )

    monitor.scan_once(0)
    monitor.scan_once(10)
    with database.session_factory() as session:
        assert list(session.query(Game)) == []

    monitor.scan_once(15)
    with database.session_factory() as session:
        game = session.query(Game).one()
        assert game.title == "Starlight"
        assert game.platform == "local"
        assert game.executable_path == r"C:\Games\Starlight\starlight.exe"
        active = SessionRepository(session).get_active(game.id)
        assert active is not None
        assert active.process_id == 410
    database.dispose()


def test_monitor_discovers_running_unlisted_steam_game_immediately(
    migrated_database: tuple[Path, str], tmp_path: Path
) -> None:
    _, database_url = migrated_database
    settings = AppSettings(database_url=database_url, log_dir=tmp_path / "logs")
    app = create_app(settings, enable_monitor=False)
    database = app.state.database
    install_directory = tmp_path / "SteamLibrary" / "steamapps" / "common" / "NewGame"
    executable = install_directory / "NewGame.exe"
    install_directory.mkdir(parents=True)
    executable.touch()
    discovery = SteamDiscovery(
        steam_path=tmp_path / "Steam",
        library_paths=(tmp_path / "SteamLibrary",),
        games=(SteamInstall(999001, "New Game", install_directory),),
    )
    source = FakeProcessSource()
    source.processes = [ProcessInfo(
        510,
        "NewGame.exe",
        str(executable),
        created_at=START,
        is_foreground=True,
        window_title="New Game",
    )]
    monitor = ProcessMonitor(
        database,
        source,
        utc_clock=lambda: START,
        app_settings=settings,
        steam_discovery=lambda _path: discovery,
        populate_artwork=False,
    )

    monitor.scan_once(0)

    with database.session_factory() as session:
        game = session.query(Game).one()
        assert game.steam_app_id == 999001
        assert game.platform == "steam"
        assert SessionRepository(session).get_active(game.id) is not None
    database.dispose()


def test_monitor_restart_grace_failure_safety_and_new_session(
    migrated_database: tuple[Path, str], tmp_path: Path
) -> None:
    _, database_url = migrated_database
    app = create_app(
        AppSettings(database_url=database_url, log_dir=tmp_path / "logs"),
        enable_monitor=False,
    )
    database = app.state.database
    with database.session_factory() as session:
        game = GameService(session).create(
            GameCreate(title="Hades", platform="steam", executable_name="hades.exe")
        )
        game_id = game.id

    source = FakeProcessSource()
    clock = [START]
    monitor = ProcessMonitor(database, source, utc_clock=lambda: clock[0])
    source.processes = [ProcessInfo(101, "HADES.EXE", created_at=START - timedelta(minutes=1))]

    monitor.scan_once(0)
    monitor.scan_once(5)
    with database.session_factory() as session:
        assert len(SessionRepository(session).list_active()) == 1

    source.processes = []
    clock[0] += timedelta(seconds=5)
    monitor.scan_once(10)
    source.error = ProcessSnapshotError("snapshot unavailable")
    monitor.scan_once(100)
    with database.session_factory() as session:
        assert len(SessionRepository(session).list_active()) == 1

    source.error = None
    source.processes = [ProcessInfo(102, "hades.exe")]
    clock[0] += timedelta(seconds=5)
    monitor.scan_once(105)
    with database.session_factory() as session:
        active = SessionRepository(session).list_active()
        assert len(active) == 1
        first_id = active[0].id

    source.processes = []
    clock[0] += timedelta(seconds=5)
    monitor.scan_once(110)
    clock[0] += timedelta(seconds=20)
    monitor.scan_once(130)
    with database.session_factory() as session:
        ended = SessionRepository(session).get(first_id)
        assert ended is not None
        assert ended.end_reason == "process_stopped"
        assert ended.duration_seconds == 10

    source.processes = [ProcessInfo(103, "hades.exe")]
    clock[0] += timedelta(seconds=1)
    monitor.scan_once(131)
    with database.session_factory() as session:
        active = SessionRepository(session).get_active(game_id)
        assert active is not None
        assert active.id != first_id
    database.dispose()


def test_startup_reconciliation_closes_stale_active_session(
    migrated_database: tuple[Path, str], tmp_path: Path
) -> None:
    _, database_url = migrated_database
    app = create_app(
        AppSettings(database_url=database_url, log_dir=tmp_path / "logs"),
        enable_monitor=False,
    )
    database = app.state.database
    with database.session_factory() as session:
        game = GameService(session).create(
            GameCreate(title="Celeste", platform="steam", executable_name="celeste.exe")
        )
        from gamedeck.services.sessions import SessionService
        SessionService(session).start_process_session(game.id, observed_at=START)

    monitor = ProcessMonitor(database, FakeProcessSource(), utc_clock=lambda: START + timedelta(hours=1))
    monitor.scan_once(0)
    with database.session_factory() as session:
        sessions = SessionRepository(session).list_active()
        assert sessions == []
        ended = SessionRepository(session).list(
            game_id=game.id, from_at=None, to_at=None, active=False, page=1, page_size=10
        )[0][0]
        assert ended.end_reason == "recovered"
        assert ended.duration_seconds == 0
    database.dispose()


def test_multiple_games_and_clean_shutdown_reconciliation(
    migrated_database: tuple[Path, str], tmp_path: Path
) -> None:
    _, database_url = migrated_database
    app = create_app(
        AppSettings(database_url=database_url, log_dir=tmp_path / "logs"),
        enable_monitor=False,
    )
    database = app.state.database
    with database.session_factory() as session:
        hades = GameService(session).create(
            GameCreate(title="Hades", platform="steam", executable_name="hades.exe")
        )
        celeste = GameService(session).create(
            GameCreate(title="Celeste", platform="steam", executable_name="celeste.exe")
        )
        ids = (hades.id, celeste.id)

    source = FakeProcessSource()
    source.processes = [ProcessInfo(1, "hades.exe"), ProcessInfo(2, "celeste.exe")]
    clock = [START]
    monitor = ProcessMonitor(database, source, utc_clock=lambda: clock[0])
    monitor.scan_once(0)
    assert monitor.status().active_game_ids == sorted(ids)

    source.processes = [ProcessInfo(1, "hades.exe")]
    clock[0] += timedelta(seconds=10)
    monitor.final_reconcile()
    with database.session_factory() as session:
        assert SessionRepository(session).get_active(ids[0]) is not None
        ended = SessionRepository(session).list(
            game_id=ids[1], from_at=None, to_at=None, active=False, page=1, page_size=10
        )[0][0]
        assert ended.end_reason == "tracker_shutdown"
    database.dispose()


def test_monitor_soak_keeps_one_session_without_success_log_spam(
    migrated_database: tuple[Path, str], tmp_path: Path, caplog
) -> None:
    _, database_url = migrated_database
    app = create_app(
        AppSettings(database_url=database_url, log_dir=tmp_path / "logs"),
        enable_monitor=False,
    )
    database = app.state.database
    with database.session_factory() as session:
        game = GameService(session).create(
            GameCreate(title="Hades", platform="steam", executable_name="hades.exe")
        )
        game_id = game.id
    source = FakeProcessSource()
    source.processes = [ProcessInfo(101, "hades.exe")]
    clock = [START]
    monitor = ProcessMonitor(database, source, utc_clock=lambda: clock[0])

    for scan in range(300):
        clock[0] = START + timedelta(seconds=scan * 5)
        monitor.scan_once(scan * 5)

    with database.session_factory() as session:
        active = SessionRepository(session).list_active()
        assert len(active) == 1
        assert active[0].game_id == game_id
        heartbeat_age = clock[0].replace(tzinfo=None) - active[0].last_seen_at
        assert timedelta(0) <= heartbeat_age < timedelta(seconds=15)
    assert not [record for record in caplog.records if record.levelname == "INFO"]
    database.dispose()


def test_settings_and_tracker_status_api(api_client: TestClient) -> None:
    initial = api_client.get("/api/v1/settings")
    assert initial.status_code == 200
    assert initial.json()["scan_interval_seconds"] == 5

    updated = api_client.patch(
        "/api/v1/settings",
        json={"tracking_enabled": False, "scan_interval_seconds": 8, "restart_grace_seconds": 20},
    )
    invalid = api_client.patch("/api/v1/settings", json={"time_zone": "Mars/Olympus"})
    status = api_client.get("/api/v1/tracker/status")

    assert updated.status_code == 200
    assert updated.json()["tracking_enabled"] is False
    assert invalid.status_code == 422
    assert status.status_code == 200
    assert status.json()["running"] is False
    assert status.json()["enabled"] is False
    assert status.json()["scan_interval_seconds"] == 8

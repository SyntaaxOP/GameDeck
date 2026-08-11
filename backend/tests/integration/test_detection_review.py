from pathlib import Path
from fastapi.testclient import TestClient
from gamedeck.schemas.game import GameCreate
from gamedeck.services.detections import AUTO_NOTE
from gamedeck.services.games import GameService
from gamedeck.services.launcher import GameLauncher

def test_detection_review_confirm_and_ignore(api_client: TestClient) -> None:
    first = api_client.post("/api/v1/games", json={"title":"Unknown Game","platform":"local","executable_name":"unknown.exe","executable_path":r"C:\Games\Unknown\unknown.exe","notes":AUTO_NOTE})
    second = api_client.post("/api/v1/games", json={"title":"Utility","platform":"local","executable_name":"utility.exe","executable_path":r"C:\Tools\utility.exe","notes":AUTO_NOTE})
    assert first.status_code == second.status_code == 201
    pending = api_client.get("/api/v1/detections").json()
    assert pending["total"] == 2

    confirmed = api_client.post(f"/api/v1/detections/{first.json()['id']}/confirm", json={"title":"Real Game"})
    ignored = api_client.post(f"/api/v1/detections/{second.json()['id']}/ignore")
    assert confirmed.status_code == 200
    assert confirmed.json()["title"] == "Real Game"
    assert ignored.status_code == 204
    assert api_client.get("/api/v1/detections").json()["total"] == 0
    rules = api_client.get("/api/v1/detections/ignored").json()
    assert rules["total"] == 1
    assert rules["items"][0]["executable_name"] == "utility.exe"

def test_launcher_uses_steam_uri_and_stored_local_path(db_session, tmp_path: Path, monkeypatch) -> None:
    steam = GameService(db_session).create(GameCreate(title="Steam Game",platform="steam",executable_name="steam-app-42.exe",steam_app_id=42))
    executable = tmp_path / "LocalGame.exe"; executable.touch()
    local = GameService(db_session).create(GameCreate(title="Local Game",platform="local",executable_name="localgame.exe",executable_path=str(executable)))
    uris: list[str] = []; commands: list[tuple[list[str], str]] = []
    monkeypatch.setattr("os.startfile", lambda uri: uris.append(uri))
    monkeypatch.setattr("subprocess.Popen", lambda command, cwd, close_fds: commands.append((command,cwd)))
    launcher = GameLauncher(db_session)
    launcher.launch(steam.id); launcher.launch(local.id)
    assert uris == ["steam://run/42"]
    assert commands == [([str(executable)], str(executable.parent))]

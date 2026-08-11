from pathlib import Path

from gamedeck.config import AppSettings
from gamedeck.integrations.steam_local import discover_installed_games
from gamedeck.models.game import Game
from gamedeck.services.steam import SteamClient, SteamService
from pydantic import SecretStr

def test_steam_configuration_requires_environment(api_client):
    assert api_client.get('/api/v1/steam/configuration').json()=={'configured':False,'steam_id':None}
    response=api_client.post('/api/v1/steam/preview',json={})
    assert response.status_code==409 and response.json()['error']['code']=='steam_not_configured'

def test_steam_preview_and_import(monkeypatch,api_client):
    api_client.app.state.settings.steam_api_key=SecretStr('secret')
    api_client.app.state.settings.steam_id='76561198000000000'
    monkeypatch.setattr(SteamClient,'fetch_owned',lambda self,key,steam_id:[{'appid':10,'name':'Counter-Strike','playtime_forever':120}])
    preview=api_client.post('/api/v1/steam/preview',json={})
    assert preview.status_code==200 and preview.json()['games'][0]['playtime_minutes']==120
    imported=api_client.post('/api/v1/steam/import',json={'items':[{'app_id':10,'name':'Counter-Strike'}]})
    repeated=api_client.post('/api/v1/steam/import',json={'items':[{'app_id':10,'name':'Counter-Strike'}]})
    assert len(imported.json()['imported_game_ids'])==1
    assert repeated.json()['skipped_app_ids']==[10]
    game=api_client.get(f"/api/v1/games/{imported.json()['imported_game_ids'][0]}").json()
    assert game['steam_app_id']==10 and game['executable_name']=='steam-app-10.exe'


def test_local_steam_discovery_and_sync(tmp_path: Path, db_session) -> None:
    steam_root = tmp_path / "Steam"
    second_library = tmp_path / "SteamLibrary"
    (steam_root / "steamapps").mkdir(parents=True)
    (second_library / "steamapps" / "common" / "Hades").mkdir(parents=True)
    escaped_library = str(second_library).replace("\\", "\\\\")
    (steam_root / "steamapps" / "libraryfolders.vdf").write_text(
        f'"libraryfolders"\n{{\n  "1"\n  {{\n    "path" "{escaped_library}"\n  }}\n}}',
        encoding="utf-8",
    )
    (second_library / "steamapps" / "appmanifest_1145360.acf").write_text(
        '"AppState"\n{\n  "appid" "1145360"\n  "name" "Hades"\n  "installdir" "Hades"\n}',
        encoding="utf-8",
    )
    (second_library / "steamapps" / "common" / "Steamworks Shared").mkdir()
    (second_library / "steamapps" / "appmanifest_228980.acf").write_text(
        '"AppState"\n{\n  "appid" "228980"\n  "name" "Steamworks Common Redistributables"\n  "installdir" "Steamworks Shared"\n}',
        encoding="utf-8",
    )

    discovery = discover_installed_games(steam_root)
    assert [game.name for game in discovery.games] == ["Hades"]

    result = SteamService(
        db_session,
        AppSettings(steam_path=steam_root),
        discovery=discovery,
    ).sync_local_library()
    assert result.discovered == 1
    assert len(result.imported_game_ids) == 1

    game = db_session.get(Game, result.imported_game_ids[0])
    assert game is not None
    assert game.steam_app_id == 1145360
    assert game.install_directory == str((second_library / "steamapps" / "common" / "Hades").resolve())

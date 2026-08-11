import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
def test_tauri_configuration_is_scoped_to_bundled_backend():
    config=json.loads((ROOT/'src-tauri'/'tauri.conf.json').read_text())
    capability=json.loads((ROOT/'src-tauri'/'capabilities'/'default.json').read_text())
    assert config['bundle']['externalBin']==['binaries/gamedeck-api']
    assert config['build']['beforeBuildCommand']=='pnpm --dir frontend build'
    assert config['build']['frontendDist']=='../frontend/dist'
    assert config['version']=='0.8.0'
    assert 'version = "0.8.0"' in (ROOT/'src-tauri'/'Cargo.toml').read_text()
    assert config['bundle']['windows']['nsis']['installMode']=='currentUser'
    assert 'http://127.0.0.1:8000' in config['app']['security']['csp']
    permission=next(item for item in capability['permissions'] if isinstance(item,dict))
    assert permission['allow']==[{'name':'binaries/gamedeck-api','sidecar':True}]

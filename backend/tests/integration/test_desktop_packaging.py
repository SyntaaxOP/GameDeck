import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
def test_tauri_configuration_is_scoped_to_bundled_backend():
    config=json.loads((ROOT/'src-tauri'/'tauri.conf.json').read_text())
    capability=json.loads((ROOT/'src-tauri'/'capabilities'/'default.json').read_text())
    assert config['bundle']['externalBin']==['binaries/gamedeck-api']
    assert config['build']['beforeBuildCommand']=='pnpm build'
    assert config['build']['frontendDist']=='../frontend/dist'
    assert config['version']=='0.8.4'
    assert 'version = "0.8.4"' in (ROOT/'src-tauri'/'Cargo.toml').read_text()
    assert config['bundle']['windows']['nsis']['installMode']=='currentUser'
    assert config['bundle']['windows']['nsis']['installerHooks']=='./windows/hooks.nsh'
    desktop_main=(ROOT/'src-tauri'/'src'/'main.rs').read_text()
    assert '#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]' in desktop_main
    assert 'open_author_github' in desktop_main
    hooks=(ROOT/'src-tauri'/'windows'/'hooks.nsh').read_text()
    assert 'NSIS_HOOK_PREINSTALL' in hooks
    assert 'gamedeck-desktop.exe' in hooks
    assert 'gamedeck-api.exe' in hooks
    assert 'http://127.0.0.1:8000' in config['app']['security']['csp']
    assert 'GAMEDECK_PORT' in (ROOT/'backend'/'src'/'gamedeck'/'sidecar.py').read_text()
    assert 'sidecar-bootstrap.log' in (ROOT/'backend'/'src'/'gamedeck'/'sidecar.py').read_text()
    assert 'stop_stale_backend' in (ROOT/'src-tauri'/'src'/'main.rs').read_text()
    assert '--noconsole' in (ROOT/'scripts'/'build-sidecar.ps1').read_text()
    permission=next(item for item in capability['permissions'] if isinstance(item,dict))
    assert permission['allow']==[{'name':'binaries/gamedeck-api','sidecar':True}]

"""Match configured games to a process snapshot."""

import ntpath
from pathlib import PureWindowsPath

from gamedeck.models.game import Game
from gamedeck.monitoring.process_source import ProcessInfo


def _normalize_path(value: str) -> str:
    return ntpath.normcase(ntpath.normpath(value.strip().strip('"')))


IGNORED_STEAM_PROCESSES = {
    "crashreporter.exe",
    "dxsetup.exe",
    "easyanticheat_eos_setup.exe",
    "steam.exe",
    "steamservice.exe",
    "steamwebhelper.exe",
    "uninstall.exe",
    "unitycrashhandler32.exe",
    "unitycrashhandler64.exe",
    "vc_redist.x64.exe",
    "vc_redist.x86.exe",
}


def _inside_directory(path: str, directory: str) -> bool:
    normalized_path = _normalize_path(path)
    normalized_directory = _normalize_path(directory)
    try:
        return ntpath.commonpath([normalized_path, normalized_directory]) == normalized_directory
    except ValueError:
        return False


def _steam_install_matches(game: Game, processes: list[ProcessInfo]) -> list[ProcessInfo]:
    if game.platform != "steam" or not game.install_directory:
        return []
    matches: list[ProcessInfo] = []
    for process in processes:
        if not process.executable_path:
            continue
        name = PureWindowsPath(process.executable_path).name.casefold()
        if name in IGNORED_STEAM_PROCESSES or name.startswith("unins"):
            continue
        if _inside_directory(process.executable_path, game.install_directory):
            matches.append(process)
    return matches


def match_games(games: list[Game], processes: list[ProcessInfo]) -> dict[int, list[ProcessInfo]]:
    by_name: dict[str, list[ProcessInfo]] = {}
    for process in processes:
        by_name.setdefault(process.executable_name.casefold(), []).append(process)

    matches: dict[int, list[ProcessInfo]] = {}
    for game in games:
        install_matches = _steam_install_matches(game, processes)
        mappings = [mapping for mapping in game.executable_mappings if mapping.active]
        if not mappings:
            mappings = [game]
        game_matches: list[ProcessInfo] = list(install_matches)
        seen_pids: set[int] = {process.pid for process in install_matches}
        for mapping in mappings:
            candidates = by_name.get(mapping.executable_name.casefold(), [])
            if not candidates:
                continue
            if mapping.executable_path:
                exact = [
                    process for process in candidates
                    if process.executable_path
                    and _normalize_path(process.executable_path) == _normalize_path(mapping.executable_path)
                ]
                if exact:
                    candidates = exact
                elif any(process.executable_path for process in candidates):
                    candidates = []
            for process in candidates:
                if process.pid not in seen_pids:
                    game_matches.append(process)
                    seen_pids.add(process.pid)
        if game_matches:
            matches[game.id] = game_matches
    return matches

"""Discover installed Steam games from local Valve manifest files."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys


PAIR_PATTERN = re.compile(r'"([^"\\]*(?:\\.[^"\\]*)*)"\s+"([^"\\]*(?:\\.[^"\\]*)*)"')
IGNORED_APP_IDS = {218, 480, 228980, 431960}
IGNORED_NAMES = {
    "source sdk base 2007",
    "spacewar",
    "steamworks common redistributables",
    "wallpaper engine",
}


@dataclass(frozen=True)
class SteamInstall:
    app_id: int
    name: str
    install_directory: Path


@dataclass(frozen=True)
class SteamDiscovery:
    steam_path: Path | None
    library_paths: tuple[Path, ...]
    games: tuple[SteamInstall, ...]


def _vdf_value(value: str) -> str:
    return value.replace(r"\\", "\\").replace(r'\"', '"')


def _pairs(text: str) -> list[tuple[str, str]]:
    return [(_vdf_value(key), _vdf_value(value)) for key, value in PAIR_PATTERN.findall(text)]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def find_steam_path(configured: Path | None = None) -> Path | None:
    candidates: list[Path] = []
    if configured:
        candidates.append(configured)
    environment_path = os.environ.get("STEAM_PATH")
    if environment_path:
        candidates.append(Path(environment_path))

    if sys.platform == "win32":
        try:
            import winreg

            registry_locations = (
                (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
            )
            for hive, key_path, value_name in registry_locations:
                try:
                    with winreg.OpenKey(hive, key_path) as key:
                        value, _kind = winreg.QueryValueEx(key, value_name)
                        candidates.append(Path(str(value)))
                except OSError:
                    continue
        except ImportError:
            pass

    program_files_x86 = os.environ.get("PROGRAMFILES(X86)")
    program_files = os.environ.get("PROGRAMFILES")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Steam")
    if program_files:
        candidates.append(Path(program_files) / "Steam")

    for candidate in candidates:
        expanded = candidate.expanduser()
        if (expanded / "steamapps").is_dir():
            return expanded.resolve()
    return None


def discover_library_paths(steam_path: Path) -> tuple[Path, ...]:
    libraries: list[Path] = [steam_path]
    manifest = steam_path / "steamapps" / "libraryfolders.vdf"
    if manifest.is_file():
        for key, value in _pairs(_read_text(manifest)):
            if key.casefold() == "path" or key.isdigit():
                candidate = Path(value)
                if (candidate / "steamapps").is_dir():
                    libraries.append(candidate.resolve())

    unique: dict[str, Path] = {}
    for library in libraries:
        unique.setdefault(os.path.normcase(str(library)), library)
    return tuple(unique.values())


def discover_installed_games(configured_path: Path | None = None) -> SteamDiscovery:
    steam_path = find_steam_path(configured_path)
    if steam_path is None:
        return SteamDiscovery(None, (), ())

    libraries = discover_library_paths(steam_path)
    discovered: dict[int, SteamInstall] = {}
    for library in libraries:
        steamapps = library / "steamapps"
        for manifest in steamapps.glob("appmanifest_*.acf"):
            try:
                values = {key.casefold(): value for key, value in _pairs(_read_text(manifest))}
                app_id = int(values["appid"])
                name = values.get("name") or f"Steam app {app_id}"
                if app_id in IGNORED_APP_IDS or name.casefold() in IGNORED_NAMES:
                    continue
                install_directory = (steamapps / "common" / values["installdir"]).resolve()
                if not install_directory.is_dir():
                    continue
                discovered[app_id] = SteamInstall(
                    app_id=app_id,
                    name=name,
                    install_directory=install_directory,
                )
            except (KeyError, ValueError, OSError):
                continue

    games = tuple(sorted(discovered.values(), key=lambda item: item.name.casefold()))
    return SteamDiscovery(steam_path, libraries, games)

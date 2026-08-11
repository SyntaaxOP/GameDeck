"""Conservative launcher-independent detection for foreground Windows games."""

from __future__ import annotations

import ntpath
from pathlib import PureWindowsPath
import re

from gamedeck.monitoring.process_source import ProcessInfo


EXCLUDED_EXECUTABLES = {
    "applicationframehost.exe",
    "battle.net.exe",
    "brave.exe",
    "chatgpt.exe",
    "chrome.exe",
    "cmd.exe",
    "code.exe",
    "codex.exe",
    "devenv.exe",
    "discord.exe",
    "excel.exe",
    "eadesktop.exe",
    "epicgameslauncher.exe",
    "explorer.exe",
    "firefox.exe",
    "galaxyclient.exe",
    "gamedeck-api.exe",
    "gamedeck-desktop.exe",
    "msedge.exe",
    "msaccess.exe",
    "ms-teams.exe",
    "notepad.exe",
    "obs64.exe",
    "opera.exe",
    "outlook.exe",
    "powerpnt.exe",
    "powershell.exe",
    "pwsh.exe",
    "python.exe",
    "pythonw.exe",
    "riotclientservices.exe",
    "slack.exe",
    "spotify.exe",
    "steam.exe",
    "steamwebhelper.exe",
    "taskmgr.exe",
    "teams.exe",
    "vlc.exe",
    "winword.exe",
    "wt.exe",
    "zoom.exe",
}


def normalize_executable_path(value: str) -> str:
    return ntpath.normcase(ntpath.normpath(value.strip().strip('"')))


def is_probable_game_candidate(process: ProcessInfo) -> bool:
    """Return true only for a sustained-foreground candidate worth auto-importing."""
    if not process.is_foreground or not process.window_title or not process.executable_path:
        return False
    path = normalize_executable_path(process.executable_path)
    name = PureWindowsPath(path).name.casefold()
    if not name.endswith(".exe") or name in EXCLUDED_EXECUTABLES:
        return False
    if name.startswith(("unins", "setup", "install", "update", "crashpad")):
        return False
    if "\\windows\\" in path or "\\appdata\\local\\temp\\" in path:
        return False
    return True


def candidate_title(process: ProcessInfo) -> str:
    """Prefer the game's visible title, with the executable stem as a stable fallback."""
    window_title = (process.window_title or "").strip()
    if 2 <= len(window_title) <= 200 and window_title.casefold() not in {
        "game",
        "unreal engine",
    }:
        return window_title
    stem = PureWindowsPath(process.executable_path or process.executable_name).stem
    words = re.sub(r"[_\-.]+", " ", stem).strip()
    return words.title() or "Detected game"

"""Safe process enumeration abstraction."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import PureWindowsPath
from typing import Protocol

import psutil


class ProcessSnapshotError(RuntimeError):
    """The entire process snapshot could not be obtained."""


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    name: str
    executable_path: str | None = None
    created_at: datetime | None = None
    is_foreground: bool = False
    window_title: str | None = None

    @property
    def executable_name(self) -> str:
        return PureWindowsPath(self.name or self.executable_path or "").name


class ProcessSource(Protocol):
    def snapshot(self) -> list[ProcessInfo]: ...


class PsutilProcessSource:
    def snapshot(self) -> list[ProcessInfo]:
        processes: list[ProcessInfo] = []
        foreground_pid, foreground_title = _foreground_window()
        try:
            iterator = psutil.process_iter(["pid", "name", "exe", "create_time"])
            for process in iterator:
                try:
                    info = process.info
                    name = info.get("name") or ""
                    executable = info.get("exe")
                    if not name and executable:
                        name = PureWindowsPath(executable).name
                    if not name:
                        continue
                    created = info.get("create_time")
                    processes.append(ProcessInfo(
                        pid=int(info["pid"]),
                        name=name,
                        executable_path=executable,
                        created_at=datetime.fromtimestamp(created, UTC) if created else None,
                        is_foreground=int(info["pid"]) == foreground_pid,
                        window_title=foreground_title if int(info["pid"]) == foreground_pid else None,
                    ))
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, OSError):
                    continue
        except (psutil.Error, OSError) as exc:
            raise ProcessSnapshotError("Windows process enumeration failed.") from exc
        return processes


def _foreground_window() -> tuple[int | None, str | None]:
    """Read the active top-level window without adding a pywin32 dependency."""
    try:
        import ctypes

        user32 = ctypes.windll.user32
        window = user32.GetForegroundWindow()
        if not window:
            return None, None
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(window, ctypes.byref(pid))
        length = user32.GetWindowTextLengthW(window)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(window, buffer, length + 1)
        title = buffer.value.strip() or None
        return int(pid.value) or None, title
    except (AttributeError, OSError, ValueError):
        return None, None

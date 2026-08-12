import json
import os
import platform
import subprocess
import winreg

import psutil
from sqlalchemy.orm import Session

from gamedeck.models.pc_profile import PCProfile
from gamedeck.schemas.pc import PCProfileResponse, PCProfileUpdate, PCSnapshotResponse, StorageVolume
from gamedeck.services.games import utc_now


def _windows_inventory() -> dict[str, object]:
    if os.name != "nt":
        return {}
    script = (
        "$os=Get-CimInstance Win32_OperatingSystem;"
        "$cpu=Get-CimInstance Win32_Processor|Select-Object -First 1;"
        "$gpu=Get-CimInstance Win32_VideoController|Where-Object {$_.Name}|Select-Object -ExpandProperty Name;"
        "$board=Get-CimInstance Win32_BaseBoard|Select-Object -First 1;"
        "[pscustomobject]@{os=$os.Caption;cpu=$cpu.Name;gpu=($gpu -join ', ');"
        "board=(($board.Manufacturer+' '+$board.Product).Trim())}|ConvertTo-Json -Compress"
    )
    try:
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=8,
            creationflags=flags,
            check=True,
        )
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {}


def _processor_name(inventory: dict[str, object]) -> str:
    detected = str(inventory.get("cpu") or "").strip()
    if detected:
        return detected
    if os.name == "nt":
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                return str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    return platform.processor() or platform.machine() or "Unknown CPU"


def _registry_value(path: str, name: str) -> str:
    if os.name != "nt":
        return ""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            return str(winreg.QueryValueEx(key, name)[0]).strip()
    except OSError:
        return ""


def _operating_system(inventory: dict[str, object]) -> str:
    detected = str(inventory.get("os") or "").strip()
    if detected:
        return detected
    product = _registry_value(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "ProductName")
    build = _registry_value(r"SOFTWARE\Microsoft\Windows NT\CurrentVersion", "CurrentBuildNumber")
    if product and build.isdigit() and int(build) >= 22000:
        product = product.replace("Windows 10", "Windows 11")
    return product or f"{platform.system()} {platform.release()}"


def _motherboard(inventory: dict[str, object]) -> str:
    detected = str(inventory.get("board") or "").strip()
    if detected:
        return detected
    path = r"HARDWARE\DESCRIPTION\System\BIOS"
    parts = [_registry_value(path, "BaseBoardManufacturer"), _registry_value(path, "BaseBoardProduct")]
    return " ".join(part for part in parts if part) or "Unknown motherboard"


def _graphics(inventory: dict[str, object]) -> str:
    detected = str(inventory.get("gpu") or "").strip()
    if detected:
        return detected
    if os.name != "nt":
        return "Unknown GPU"
    names: list[str] = []
    root_path = r"SYSTEM\CurrentControlSet\Control\Video"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, root_path) as root:
            index = 0
            while True:
                try:
                    adapter_key = winreg.EnumKey(root, index)
                except OSError:
                    break
                index += 1
                name = _registry_value(f"{root_path}\\{adapter_key}\\0000", "DriverDesc")
                if name and name not in names:
                    names.append(name)
    except OSError:
        pass
    return ", ".join(names) or "Unknown GPU"


def _storage_volumes() -> list[StorageVolume]:
    volumes: list[StorageVolume] = []
    seen: set[str] = set()
    for partition in psutil.disk_partitions(all=False):
        device = partition.device.casefold()
        if device in seen:
            continue
        seen.add(device)
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (OSError, PermissionError):
            continue
        volumes.append(StorageVolume(name=partition.device or partition.mountpoint, total_gb=round(usage.total / (1024**3))))
    if not volumes:
        root = os.path.abspath(os.sep)
        usage = psutil.disk_usage(root)
        volumes.append(StorageVolume(name=root, total_gb=round(usage.total / (1024**3))))
    return volumes


class PCService:
    def __init__(self, session: Session):
        self.session = session

    def get(self) -> PCProfileResponse | None:
        item = self.session.get(PCProfile, 1)
        return PCProfileResponse.model_validate(item, from_attributes=True) if item else None

    def update(self, payload: PCProfileUpdate) -> PCProfileResponse:
        item = self.session.get(PCProfile, 1) or PCProfile(id=1, name=payload.name, updated_at=utc_now())
        self.session.add(item)
        for key, value in payload.model_dump().items():
            setattr(item, key, value)
        item.updated_at = utc_now()
        self.session.commit()
        return PCProfileResponse.model_validate(item, from_attributes=True)

    def snapshot(self) -> PCSnapshotResponse:
        inventory = _windows_inventory()
        volumes = _storage_volumes()
        return PCSnapshotResponse(
            operating_system=_operating_system(inventory),
            cpu_label=_processor_name(inventory),
            gpu_label=_graphics(inventory),
            motherboard=_motherboard(inventory),
            logical_cpu_count=psutil.cpu_count() or 0,
            memory_gb=round(psutil.virtual_memory().total / (1024**3)),
            total_storage_gb=sum(volume.total_gb for volume in volumes),
            storage_volumes=volumes,
        )

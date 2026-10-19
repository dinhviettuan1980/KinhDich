"""Thông tin hệ thống cho bản tin status (đọc từ /proc, /sys trên Raspberry Pi)."""
import os
import shutil
import time
from pathlib import Path

_BOOT = time.time()


def cpu_temp() -> float | None:
    p = Path("/sys/class/thermal/thermal_zone0/temp")
    try:
        return round(int(p.read_text()) / 1000, 1)
    except (OSError, ValueError):
        return None


def net_info() -> tuple[str, int | None]:
    """('wifi'|'4g'|'eth'|'unknown', rssi dBm)."""
    try:
        lines = Path("/proc/net/wireless").read_text().splitlines()[2:]
        if lines:
            rssi = int(float(lines[0].split()[3].rstrip(".")))
            return "wifi", rssi
    except (OSError, ValueError, IndexError):
        pass
    try:
        ifaces = os.listdir("/sys/class/net")
    except OSError:
        return "unknown", None
    if any(i.startswith(("wwan", "usb", "ppp")) for i in ifaces):
        return "4g", None
    if any(i.startswith(("eth", "en")) for i in ifaces):
        return "eth", None
    return "unknown", None


def uptime() -> int:
    try:
        return int(float(Path("/proc/uptime").read_text().split()[0]))
    except (OSError, ValueError):
        return int(time.time() - _BOOT)


def disk_free_mb(path: Path) -> int:
    try:
        return shutil.disk_usage(path).free // (1024 * 1024)
    except OSError:
        return -1

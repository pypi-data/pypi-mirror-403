import shutil

from . import utils


def get_uptime_info():

    try:
        return int(utils.read_file("/proc/uptime").split()[0])
    except Exception:
        return 0


def get_memory_info() -> dict:

    meminfo = {}

    with open("/proc/meminfo", encoding="utf-8") as f:

        for line in f:
            key, value = line.split(":", 1)
            meminfo[key] = int(value.strip().split()[0]) * 1024  # kB -> bytes

    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", 0)
    used = total - available

    return {
        "total": utils.bytes_to_gigabyte(total),
        "used": utils.bytes_to_gigabyte(used),
        "available": utils.bytes_to_gigabyte(available),
        "usage_percent": round(used / total * 100, 2) if total else 0,
    }


def get_disk_info(path: str = "/") -> dict:

    usage = shutil.disk_usage(path)

    return {
        "total": utils.bytes_to_gigabyte(usage.total),
        "used": utils.bytes_to_gigabyte(usage.used),
        "available": utils.bytes_to_gigabyte(usage.free),
        "usage_percent": round(usage.used / usage.total * 100, 2),
    }

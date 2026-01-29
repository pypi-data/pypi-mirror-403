import shutil
from os import environ

from loguru import logger

from . import utils

DEBUG = environ.get("DEBUG")


def get_uptime_info() -> int | None:

    try:

        return int(float(utils.read_file("/proc/uptime").split()[0]))

    except Exception as e:

        if DEBUG:
            logger.exception(e)
        else:
            logger.error(e)

        return None


def get_memory_info() -> dict | None:

    try:

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

    except Exception as e:

        if DEBUG:
            logger.exception(e)
        else:
            logger.error(e)

        return None


def get_disk_info(path: str = "/") -> dict | None:

    try:

        usage = shutil.disk_usage(path)

        return {
            "total": utils.bytes_to_gigabyte(usage.total),
            "used": utils.bytes_to_gigabyte(usage.used),
            "available": utils.bytes_to_gigabyte(usage.free),
            "usage_percent": round(usage.used / usage.total * 100, 2),
        }

    except Exception as e:

        if DEBUG:
            logger.exception(e)
        else:
            logger.error(e)

        return None

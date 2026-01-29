from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

import requests

BASE_URL = "https://api.64clouds.com/v1"

GB = Decimal(1024) ** 3

TWO_PLACES = Decimal("0.01")


@dataclass(slots=True)
class BandwagonConfig:
    veid: str
    api_key: str
    timeout: int = 10


class BandwagonClient:

    def __init__(self, config: BandwagonConfig, requests_parameters: dict | None = None) -> None:
        self.config = config
        self.requests_parameters = requests_parameters

    def _request(self, *, action: str) -> dict[str, Any]:
        url = f"{BASE_URL}/{action}"
        params = {
            "veid": self.config.veid,
            "api_key": self.config.api_key,
        }

        # HTTP 请求头
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

        requests_parameters: dict = {
            "headers": {"User-Agent": user_agent},
            # "proxies": {
            #     "http": "http://127.0.0.1:1080",
            #     "https": "http://127.0.0.1:1080",
            # },
        }
        if self.requests_parameters:
            requests_parameters.update(self.requests_parameters)

        resp = requests.get(url, params=params, timeout=self.config.timeout, **requests_parameters)
        resp.raise_for_status()
        data: dict = resp.json()

        if data.get("error"):
            raise RuntimeError(data.get("message"))

        return data

    # -------------------------
    # 核心接口
    # -------------------------

    def get_live_info(self) -> dict[str, Any]:
        """实时运行状态（CPU / 磁盘 / 内存 / 在线状态）"""
        return self._request(action="getLiveServiceInfo")

    def get_service_info(self) -> dict[str, Any]:
        """VPS 基本信息"""
        return self._request(action="getServiceInfo")


# --------------------------------
# 业务层封装
# --------------------------------


def format_disk(info: dict) -> str:

    # 硬盘大小 (单位GB)
    total = int(info["ve_disk_quota_gb"])

    # 使用量 (单位GB)
    used = info["ve_used_disk_space_b"] / (1024 * 1024 * 1024)

    # 使用率
    usage = (info["ve_used_disk_space_b"] / (total * 1024 * 1024 * 1024)) * 100

    return f"{used:.2f}/{total:.0f} GB ({usage:.2f}%)"


def format_bandwidth(info: dict) -> str:

    # 带宽大小 (单位GB)
    total = info["plan_monthly_data"] / 1024 / 1024 / 1024

    # 使用量 (单位GB)
    used = info["data_counter"] / 1024 / 1024 / 1024

    # 使用率
    usage = (info["data_counter"] / info["plan_monthly_data"]) * 100

    return f"{used:.2f}/{total:.0f} GB ({usage:.2f}%)"


def expiration_date(info: dict) -> str:
    # 过期时间
    # 通过 getLiveServiceInfo 获取 data_next_reset 字段 (秒级时间戳)
    # 将时间戳转为 UTC+8 时间
    date = datetime.fromtimestamp(info["data_next_reset"], tz=timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    return date


# --------------------------------------------------------------------------------------------------


def _to_gb(value: int | str | float) -> Decimal:
    """字节转 GB（Decimal 精确）"""
    return (Decimal(str(value)) / GB).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def bandwidth_allowance(info: dict) -> dict[str, Decimal]:
    """
    计算带宽配额使用情况（精确计算，保留两位小数）
    返回值单位：GB / %
    """

    total = _to_gb(info["plan_monthly_data"])
    used = _to_gb(info["data_counter"])
    available = total - used

    if total == 0:
        usage_percent = Decimal("0.00")
    else:
        usage_percent = (used / total * 100).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    return {
        "total": total,  # Decimal('123.45')
        "used": used,  # Decimal('67.89')
        "available": available,
        "usage_percent": usage_percent,  # Decimal('54.32')
    }

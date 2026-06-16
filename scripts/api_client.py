# -*- coding: utf-8 -*-
"""通过 HTTP API 提交日报（同事侧）。"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.schemas import prepare_report_payload
from report_io import get_api_token, get_api_url, get_username


def submit_daily_via_api(report: dict[str, Any]) -> dict[str, Any]:
    """
    将日报 POST 到团队 API。

    @param report 日报 JSON（会先按契约清洗）
    @returns API 响应 JSON
    """
    payload = prepare_report_payload(report)
    base_url = get_api_url().rstrip("/")
    token = get_api_token()
    username = get_username()

    if payload["user"] != username:
        raise ValueError(
            f"report.user={payload['user']} 与配置 username={username} 不一致"
        )

    url = f"{base_url}/api/v1/daily-reports"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=int(os.getenv("REPORT_API_TIMEOUT", "30")),
        )
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError(
            f"无法连接日报 API：{base_url}。"
            " 若不在公司内网，请先连接公司 VPN 再提交；"
            " 仍失败请联系 Frank 检查 API 是否在运行。"
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            f"连接日报 API 超时：{base_url}。"
            " 请确认已连 VPN 或内网，并联系 Frank 确认服务状态。"
        ) from exc
    if response.status_code >= 400:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass
        raise RuntimeError(f"API 提交失败 ({response.status_code}): {detail}")

    return response.json()

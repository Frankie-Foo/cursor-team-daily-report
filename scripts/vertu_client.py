# -*- coding: utf-8 -*-
"""Vertu CLI 封装（日报 / Vemory）。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def resolve_vertu_command() -> str:
    """
    解析 vertu 可执行文件路径。

    @returns vertu 命令路径
    """
    override = os.getenv("VERTU_COMMAND", "").strip()
    if override:
        return override
    npm_cmd = Path.home() / "AppData" / "Roaming" / "npm" / "vertu.cmd"
    if npm_cmd.exists():
        return str(npm_cmd)
    discovered = subprocess.which("vertu")
    if discovered:
        return discovered
    raise FileNotFoundError(
        "未找到 vertu CLI。请安装 @vertu-tech/vps-cli 或设置 VERTU_COMMAND"
    )


def run_vertu_json(args: list[str], timeout: int = 120) -> dict[str, Any]:
    """
    执行 vertu 子命令并解析 JSON  stdout。

    @param args vertu 子命令参数（不含 vertu 本身）
    @param timeout 超时秒数
    @returns 解析后的 JSON 对象
    """
    cmd = [resolve_vertu_command(), *args]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "vertu 命令失败"
        raise RuntimeError(detail)
    stdout = proc.stdout.strip()
    if not stdout:
        return {}
    return json.loads(stdout)


def fetch_vertu_daily_summary(user_id: int, report_date: str) -> dict[str, Any]:
    """
    拉取 Vertu 业务日报。

    @param user_id Odoo res.users ID
    @param report_date YYYY-MM-DD
    @returns user-summary JSON
    """
    return run_vertu_json(
        [
            "odoo",
            "daily-report",
            "user-summary",
            "--user-id",
            str(user_id),
            "--start-time",
            report_date,
            "--end-time",
            report_date,
        ]
    )


def fetch_vemory_meetings(
    user_id: int,
    start_date: str,
    end_date: str | None = None,
    max_meetings: int = 30,
) -> dict[str, Any]:
    """
    拉取 Vemory 会议列表。

    @param user_id Odoo res.users ID
    @param start_date 起始日期
    @param end_date 结束日期，默认同 start_date
    @param max_meetings 最大条数
    @returns vemory meetings JSON
    """
    end = end_date or start_date
    return run_vertu_json(
        [
            "odoo",
            "vemory",
            "meetings",
            "--user-id",
            str(user_id),
            "--start-date",
            start_date,
            "--end-date",
            end,
            "--max-meetings",
            str(max_meetings),
        ],
        timeout=180,
    )

# -*- coding: utf-8 -*-
"""
Cursor 团队日报 — MCP Server（本地 stdio）。

让同事在 Cursor / Claude Code / Trae 等 MCP 客户端里直接调用，
一键总结当天 Cursor 工作（可选合并 Vertu + Vemory）并 POST 到团队 API。

依赖：pip install "mcp[cli]>=1.2.0"
运行：python mcp/server.py   （由 MCP 客户端以 stdio 方式拉起）

工具一览：
  - check_setup              检查本机配置 + API 连通 + vertu 登录
  - test_api                 健康检查团队 API
  - preview_sessions         预览当天 Cursor 会话列表（不生成日报、不提交）
  - generate_cursor_daily    解析当天 Cursor 会话，返回日报 JSON（不提交）
  - generate_unified_daily   解析 Vertu+Vemory+Cursor，返回统一日报 JSON（不提交）
  - submit_daily_report      把日报 JSON POST 到团队 API
  - submit_my_cursor_daily   一键：Cursor 日报生成 + 提交
  - submit_my_unified_daily  一键：统一日报生成 + 提交
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
for p in (str(SCRIPTS), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import requests  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

from api_client import submit_daily_via_api  # noqa: E402
from build_unified_daily import build_unified_report  # noqa: E402
from parse_transcripts import (  # noqa: E402
    build_daily_report,
    collect_session_files,
    discover_transcripts_dir,
    merge_session_parts,
    parse_session_file,
    resolve_target_date,
)
from publish_daily import refine_summary_with_ai  # noqa: E402
from report_io import (  # noqa: E402
    get_api_token,
    get_api_url,
    get_cursor_workspace,
    get_username,
    load_user_profile,
    repo_root,
)

mcp = FastMCP("cursor-team-daily-report")

_LOG_DIR = ROOT / "logs"
_LOG_FILE = _LOG_DIR / "mcp_submissions.log"


def _log(line: str) -> None:
    """追加一行提交日志。"""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        with _LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(line.rstrip() + "\n")
    except Exception:
        pass


def _err(exc: Exception) -> dict[str, Any]:
    """把异常转成结构化错误返回，避免 MCP 直接崩。"""
    return {"ok": False, "error": str(exc), "type": type(exc).__name__}


def _parse_sessions(date: str, workspace: str, username: str, tz: str) -> list[dict[str, Any]]:
    """解析指定日期的 Cursor 会话列表。"""
    target_date = resolve_target_date(date, tz)
    ws = workspace.strip() or get_cursor_workspace()
    ws_path = Path(ws).resolve()
    transcripts_dir = discover_transcripts_dir(str(ws_path))

    sessions: list[dict[str, Any]] = []
    for main_file, subagent_files in collect_session_files(transcripts_dir):
        main_parsed = parse_session_file(main_file, target_date, tz)
        extras = [parse_session_file(p, target_date, tz) for p in subagent_files]
        extras = [item for item in extras if item]
        merged = merge_session_parts(main_parsed, extras)
        if merged:
            sessions.append(merged)
    return sessions


def _cursor_report(date: str, workspace: str, username: str, tz: str) -> dict[str, Any]:
    """生成 Cursor-only 日报 JSON。"""
    target_date = resolve_target_date(date, tz)
    ws = workspace.strip() or get_cursor_workspace()
    ws_path = Path(ws).resolve()
    sessions = _parse_sessions(date, workspace, username, tz)
    report = build_daily_report(sessions, target_date, username, tz, ws_path)
    report = refine_summary_with_ai(report)
    report.pop("_raw_sessions", None)
    report["report_kind"] = "cursor"
    return report


def _unified_report(
    date: str,
    workspace: str,
    username: str,
    tz: str,
    skip_vertu: bool,
    skip_vemory: bool,
) -> dict[str, Any]:
    """生成 Vertu+Vemory+Cursor 统一日报 JSON（复用 build_unified_daily 逻辑）。"""
    profile = load_user_profile()
    user = username.strip() or get_username()
    display_name = (profile.get("display_name") or user)
    odoo_user_id = int(profile.get("odoo_user_id") or 0)
    ws = workspace.strip() or get_cursor_workspace()

    ns = argparse.Namespace(
        date=date,
        timezone=tz,
        username=user,
        display_name=display_name,
        odoo_user_id=odoo_user_id,
        workspace=ws,
        skip_vertu=skip_vertu,
        skip_vemory=skip_vemory,
        skip_cursor=False,
    )
    report = build_unified_report(ns)
    report.pop("_raw_sessions", None)
    return report


def _apply_summary_override(report: dict[str, Any], override: str) -> dict[str, Any]:
    """用 Agent 精炼后的摘要覆盖 daily_summary。"""
    if override.strip():
        report["daily_summary"] = override.strip()
        report["daily_summary_refined_by"] = "agent"
    return report


@mcp.tool()
def check_setup() -> dict[str, Any]:
    """
    检查本机日报配置是否就绪：用户名、工作区、API 地址、Token、API 连通、vertu 登录。

    @returns 各配置项状态与问题清单
    """
    result: dict[str, Any] = {
        "username": "",
        "cursor_workspace": "",
        "api_url": "",
        "has_token": False,
        "api_reachable": False,
        "vertu_logged_in": False,
        "ok": False,
        "problems": [],
    }
    try:
        result["username"] = get_username()
    except Exception as exc:
        result["problems"].append(f"username: {exc}")

    try:
        result["cursor_workspace"] = get_cursor_workspace()
    except Exception as exc:
        result["problems"].append(f"cursor_workspace: {exc}")

    try:
        result["api_url"] = get_api_url()
    except Exception as exc:
        result["problems"].append(f"api_url: {exc}")
        return _finalize_setup(result)

    try:
        get_api_token()
        result["has_token"] = True
    except Exception as exc:
        result["problems"].append(f"token: {exc}")

    # API 健康检查（不需要 Token）
    try:
        resp = requests.get(
            f"{result['api_url'].rstrip('/')}/api/v1/health",
            timeout=10,
        )
        result["api_reachable"] = resp.status_code == 200
        if not result["api_reachable"]:
            result["problems"].append(f"api health: HTTP {resp.status_code}")
    except Exception as exc:
        result["problems"].append(f"api health: {exc}")

    # vertu 登录检查
    try:
        import shutil
        import subprocess

        vertu_bin = shutil.which("vertu") or shutil.which("vertu.cmd")
        if not vertu_bin:
            result["problems"].append("vertu: CLI 未安装（npm i -g @vertu-tech/vps-cli）")
        else:
            proc = subprocess.run(
                [vertu_bin, "whoami"], capture_output=True, text=True, timeout=15
            )
            out = (proc.stdout or "") + (proc.stderr or "")
            result["vertu_logged_in"] = proc.returncode == 0 and "ok" in out
            if not result["vertu_logged_in"]:
                result["problems"].append("vertu: 未登录（运行 vertu login）")
    except Exception as exc:
        result["problems"].append(f"vertu: {exc}")

    return _finalize_setup(result)


def _finalize_setup(result: dict[str, Any]) -> dict[str, Any]:
    """汇总 problems 得出 ok。"""
    result["ok"] = not result["problems"]
    return result


@mcp.tool()
def test_api() -> dict[str, Any]:
    """
    健康检查团队日报 API（GET /api/v1/health）。

    @returns {ok, status_code, body}
    """
    try:
        base = get_api_url().rstrip("/")
        resp = requests.get(f"{base}/api/v1/health", timeout=10)
        body = resp.text
        try:
            body = resp.json()
        except Exception:
            pass
        return {"ok": resp.status_code == 200, "status_code": resp.status_code, "body": body}
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def preview_sessions(
    date: str = "today",
    workspace: str = "",
    timezone: str = "Asia/Shanghai",
) -> dict[str, Any]:
    """
    预览当天（或指定日期）的 Cursor 会话列表，轻量、不生成日报、不提交。

    用来在提交前确认今天有哪些会话被识别到。

    @param date 目标日期，"today" 或 YYYY-MM-DD
    @param workspace Cursor 工作区路径，留空读 config/user.json
    @param timezone 时区
    @returns {date, total_sessions, total_turns, sessions:[{summary,turns,outcome,tools_used}]}
    """
    try:
        user = get_username()
        sessions = _parse_sessions(date, workspace, user, timezone)
        total_turns = sum(s.get("turns", 0) for s in sessions)
        light = [
            {
                "summary": s.get("summary", "未命名会话"),
                "turns": s.get("turns", 0),
                "outcome": s.get("outcome", "unknown"),
                "tools_used": s.get("tools_used", [])[:6],
            }
            for s in sessions
        ]
        return {
            "date": resolve_target_date(date, timezone).isoformat(),
            "total_sessions": len(sessions),
            "total_turns": total_turns,
            "sessions": light,
        }
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def generate_cursor_daily(
    date: str = "today",
    workspace: str = "",
    username: str = "",
    timezone: str = "Asia/Shanghai",
) -> dict[str, Any]:
    """
    解析当天 Cursor 会话，生成 Cursor 日报 JSON（不提交）。

    可在此基础上改写 daily_summary，再调用 submit_daily_report 提交。

    @param date 目标日期，"today" 或 YYYY-MM-DD
    @param workspace Cursor 工作区路径，留空读 config/user.json
    @param username 用户名，留空读 config/user.json
    @param timezone 时区
    @returns 日报 JSON（含 daily_summary、sessions、key_topics）
    """
    try:
        user = username.strip() or get_username()
        return _cursor_report(date, workspace, user, timezone)
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def generate_unified_daily(
    date: str = "today",
    workspace: str = "",
    username: str = "",
    timezone: str = "Asia/Shanghai",
    skip_vertu: bool = False,
    skip_vemory: bool = False,
) -> dict[str, Any]:
    """
    生成统一日报 JSON：Vertu 业务 + Vemory 会议 + Cursor 工作（不提交）。

    需要 config/user.json 里有 odoo_user_id，且本机已 vertu login。
    Vertu/Vemory 拉取失败时会返回错误，可改用 generate_cursor_daily 只交 Cursor 部分。

    @param date 目标日期，"today" 或 YYYY-MM-DD
    @param workspace Cursor 工作区路径，留空读 config/user.json
    @param username 用户名，留空读 config/user.json
    @param timezone 时区
    @param skip_vertu 跳过 Vertu 业务日报
    @param skip_vemory 跳过 Vemory 会议
    @returns 统一日报 JSON（含 sections.vertu / sections.vemory / sections.cursor）
    """
    try:
        user = username.strip() or get_username()
        return _unified_report(date, workspace, user, timezone, skip_vertu, skip_vemory)
    except Exception as exc:
        return _err(exc)


@mcp.tool()
def submit_daily_report(
    report: dict[str, Any],
    daily_summary_override: str = "",
) -> dict[str, Any]:
    """
    把日报 JSON 提交（POST）到团队日报 API。

    通常配合 generate_cursor_daily / generate_unified_daily 使用：
    先生成，必要时改写 daily_summary（或通过 daily_summary_override 传入精炼版），再提交。
    report.user 必须与 config/user.json 的 username 一致。

    @param report 日报 JSON（generate_* 的返回值）
    @param daily_summary_override 可选，用 Agent 精炼后的摘要覆盖 report.daily_summary
    @returns API 响应
    """
    try:
        report = _apply_summary_override(report, daily_summary_override)
        resp = submit_daily_via_api(report)
        _log(
            json.dumps(
                {
                    "ts": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
                    "user": report.get("user"),
                    "date": report.get("date"),
                    "report_kind": report.get("report_kind", "unknown"),
                    "ok": True,
                    "api": resp,
                },
                ensure_ascii=False,
            )
        )
        return {"ok": True, "api": resp}
    except Exception as exc:
        _log(
            json.dumps(
                {
                    "ts": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
                    "user": (report or {}).get("user") if isinstance(report, dict) else None,
                    "ok": False,
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return _err(exc)


@mcp.tool()
def submit_my_cursor_daily(
    date: str = "today",
    workspace: str = "",
    username: str = "",
    timezone: str = "Asia/Shanghai",
    daily_summary_override: str = "",
) -> dict[str, Any]:
    """
    一键生成并提交今天（或指定日期）的 Cursor 日报。

    等价于 generate_cursor_daily + submit_daily_report 串行调用。
    适合自动化定时触发。

    @param date 目标日期，"today" 或 YYYY-MM-DD
    @param workspace Cursor 工作区路径，留空读 config/user.json
    @param username 用户名，留空读 config/user.json
    @param timezone 时区
    @param daily_summary_override 可选，Agent 精炼后的摘要覆盖
    @returns 提交结果（user、date、total_sessions、api 响应）
    """
    try:
        user = username.strip() or get_username()
        report = _cursor_report(date, workspace, user, timezone)
        report = _apply_summary_override(report, daily_summary_override)
        api_response = submit_daily_via_api(report)
        result = {
            "ok": True,
            "user": user,
            "date": report.get("date"),
            "report_kind": "cursor",
            "total_sessions": report.get("total_sessions", 0),
            "total_turns": report.get("total_turns", 0),
            "submitted": True,
            "api": api_response,
        }
        _log(json.dumps(result, ensure_ascii=False))
        return result
    except Exception as exc:
        _log(
            json.dumps(
                {
                    "ts": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
                    "ok": False,
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return _err(exc)


@mcp.tool()
def submit_my_unified_daily(
    date: str = "today",
    workspace: str = "",
    username: str = "",
    timezone: str = "Asia/Shanghai",
    skip_vertu: bool = False,
    skip_vemory: bool = False,
    daily_summary_override: str = "",
) -> dict[str, Any]:
    """
    一键生成并提交今天（或指定日期）的统一日报（Vertu+Vemory+Cursor）。

    需要 odoo_user_id 且 vertu 已登录。任一外部源失败会返回错误，
    此时建议改用 submit_my_cursor_daily 只交 Cursor 部分。

    @param date 目标日期，"today" 或 YYYY-MM-DD
    @param workspace Cursor 工作区路径，留空读 config/user.json
    @param username 用户名，留空读 config/user.json
    @param timezone 时区
    @param skip_vertu 跳过 Vertu
    @param skip_vemory 跳过 Vemory
    @param daily_summary_override 可选，Agent 精炼后的摘要覆盖
    @returns 提交结果（user、date、sections 概览、api 响应）
    """
    try:
        user = username.strip() or get_username()
        report = _unified_report(date, workspace, user, timezone, skip_vertu, skip_vemory)
        report = _apply_summary_override(report, daily_summary_override)
        api_response = submit_daily_via_api(report)
        sections = report.get("sections") or {}
        result = {
            "ok": True,
            "user": user,
            "date": report.get("date"),
            "report_kind": "unified",
            "total_sessions": report.get("total_sessions", 0),
            "vertu_tasks": len((sections.get("vertu") or {}).get("today_tasks") or []),
            "vemory_meetings": (sections.get("vemory") or {}).get("total_meetings", 0),
            "submitted": True,
            "api": api_response,
        }
        _log(json.dumps(result, ensure_ascii=False))
        return result
    except Exception as exc:
        _log(
            json.dumps(
                {
                    "ts": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
                    "ok": False,
                    "error": str(exc),
                },
                ensure_ascii=False,
            )
        )
        return _err(exc)


if __name__ == "__main__":
    mcp.run()

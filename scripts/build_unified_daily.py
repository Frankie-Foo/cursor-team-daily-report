# -*- coding: utf-8 -*-
"""
统一日报：Vertu 业务日报 + Vemory 会议 + Cursor 工作 → 合并 POST。

用法:
  python build_unified_daily.py --date today --api-only
  python build_unified_daily.py --date 2026-06-12 --odoo-user-id 13063 --username 于冰 --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api_client import submit_daily_via_api
from parse_transcripts import (
    build_daily_report,
    collect_session_files,
    discover_transcripts_dir,
    infer_topics,
    merge_session_parts,
    parse_session_file,
    resolve_target_date,
)
from publish_daily import refine_summary_with_ai
from report_io import get_cursor_workspace, get_username, load_user_profile, write_json
from unified_report import (
    build_highlights,
    parse_vemory_meetings,
    parse_vertu_tasks,
    render_unified_markdown,
)
from vertu_client import fetch_vemory_meetings, fetch_vertu_daily_summary


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="生成并提交统一日报")
    parser.add_argument("--date", default="today", help="目标日期")
    parser.add_argument("--timezone", default="Asia/Shanghai", help="时区")
    parser.add_argument("--username", default="", help="报告用户名")
    parser.add_argument("--display-name", default="", help="展示名")
    parser.add_argument("--odoo-user-id", type=int, default=0, help="Odoo user id")
    parser.add_argument("--workspace", default="", help="Cursor 工作区")
    parser.add_argument("--skip-vertu", action="store_true", help="跳过 Vertu")
    parser.add_argument("--skip-vemory", action="store_true", help="跳过 Vemory")
    parser.add_argument("--skip-cursor", action="store_true", help="跳过 Cursor")
    parser.add_argument("--api-only", action="store_true", help="POST 到 API")
    parser.add_argument("--dry-run", action="store_true", help="只输出 JSON 不提交")
    parser.add_argument("--output", default="", help="写入 JSON 路径")
    return parser.parse_args()


def resolve_profile(args: argparse.Namespace) -> dict[str, Any]:
    """合并 CLI 与 user.json 配置。"""
    profile = load_user_profile()
    username = args.username.strip() or str(profile.get("username") or "").strip() or get_username()
    display_name = args.display_name.strip() or str(profile.get("display_name") or username)
    odoo_user_id = args.odoo_user_id or int(profile.get("odoo_user_id") or 0)
    return {
        "username": username,
        "display_name": display_name,
        "odoo_user_id": odoo_user_id,
        "timezone": str(profile.get("timezone") or args.timezone),
    }


def fetch_cursor_section(
    target_date,
    username: str,
    workspace: str,
    timezone: str,
) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    """
    解析 Cursor transcripts。

    @returns (summary_text, sessions, raw_report)
    """
    workspace_path = Path(workspace).resolve()
    transcripts_dir = discover_transcripts_dir(str(workspace_path))
    sessions_parsed = []
    for main_file, subagent_files in collect_session_files(transcripts_dir):
        main_parsed = parse_session_file(main_file, target_date, timezone)
        extra_parsed = [
            parse_session_file(path, target_date, timezone)
            for path in subagent_files
        ]
        extra_parsed = [item for item in extra_parsed if item]
        merged = merge_session_parts(main_parsed, extra_parsed)
        if merged:
            sessions_parsed.append(merged)

    report = build_daily_report(
        sessions_parsed,
        target_date,
        username,
        timezone,
        workspace_path,
    )
    report = refine_summary_with_ai(report)
    summary = str(report.get("daily_summary") or "")
    sessions = report.get("sessions") or []
    return summary, sessions, report


def build_unified_report(args: argparse.Namespace) -> dict[str, Any]:
    """构建统一日报 JSON。"""
    profile = resolve_profile(args)
    username = profile["username"]
    display_name = profile["display_name"]
    odoo_user_id = profile["odoo_user_id"]
    timezone = profile["timezone"]
    target_date = resolve_target_date(args.date, timezone)
    date_text = target_date.isoformat()

    vertu_raw: dict[str, Any] = {}
    vertu_tasks: list[dict[str, Any]] = []
    tomorrow_plans: list[str] = []
    okr: dict[str, Any] = {}

    if not args.skip_vertu:
        if not odoo_user_id:
            raise ValueError("缺少 odoo_user_id，请在 config/user.json 配置或传 --odoo-user-id")
        vertu_raw = fetch_vertu_daily_summary(odoo_user_id, date_text)
        vertu_tasks, tomorrow_plans, okr = parse_vertu_tasks(vertu_raw)

    vemory_raw: dict[str, Any] = {}
    vemory_meetings: list[dict[str, Any]] = []
    if not args.skip_vemory:
        if not odoo_user_id:
            raise ValueError("缺少 odoo_user_id，无法拉 Vemory")
        vemory_raw = fetch_vemory_meetings(odoo_user_id, date_text, date_text)
        vemory_meetings = parse_vemory_meetings(vemory_raw)

    cursor_summary = ""
    cursor_sessions: list[dict[str, Any]] = []
    cursor_report: dict[str, Any] = {}
    all_files: list[str] = []
    total_sessions = 0
    total_turns = 0

    if not args.skip_cursor:
        workspace = args.workspace.strip() or get_cursor_workspace()
        cursor_summary, cursor_sessions, cursor_report = fetch_cursor_section(
            target_date,
            username,
            workspace,
            timezone,
        )
        all_files = cursor_report.get("all_files_modified") or []
        total_sessions = int(cursor_report.get("total_sessions") or 0)
        total_turns = int(cursor_report.get("total_turns") or 0)

    highlights = build_highlights(vertu_tasks, okr, vemory_meetings, cursor_sessions)
    daily_summary = render_unified_markdown(
        display_name,
        date_text,
        vertu_tasks,
        tomorrow_plans,
        okr,
        vemory_meetings,
        cursor_summary,
        cursor_sessions,
        highlights,
    )

    topics = infer_topics(
        *[t.get("title", "") for t in vertu_tasks],
        *[m.get("name", "") for m in vemory_meetings],
        *[s.get("summary", "") for s in cursor_sessions],
    )

    generated_at = datetime.now(ZoneInfo(timezone)).isoformat()
    return {
        "user": username,
        "date": date_text,
        "generated_at": generated_at,
        "report_kind": "unified",
        "total_sessions": total_sessions,
        "total_turns": total_turns,
        "daily_summary": daily_summary,
        "key_topics": topics[:10],
        "all_files_modified": all_files,
        "sessions": cursor_sessions,
        "sections": {
            "vertu": {
                "odoo_user_id": odoo_user_id,
                "okr": okr,
                "today_tasks": vertu_tasks,
                "tomorrow_plans": tomorrow_plans,
                "submitted": bool(vertu_raw.get("daily_reports")),
            },
            "vemory": {
                "total_meetings": len(vemory_meetings),
                "meetings": vemory_meetings,
            },
            "cursor": {
                "summary": cursor_summary,
                "total_sessions": total_sessions,
                "total_turns": total_turns,
                "sessions": cursor_sessions,
            },
            "highlights": highlights,
        },
    }


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    report = build_unified_report(args)

    out_path = args.output.strip()
    if out_path:
        write_json(Path(out_path), report)

    result: dict[str, Any] = {
        "user": report["user"],
        "date": report["date"],
        "report_kind": "unified",
    }

    if args.dry_run:
        result["dry_run"] = True
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    if args.api_only:
        api_response = submit_daily_via_api(report)
        result["submitted"] = True
        result["via"] = "api"
        result["api"] = api_response
    else:
        result["submitted"] = False
        result["preview"] = report["daily_summary"][:500]

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
拉取团队指定日期区间的 Vertu 日报 + Vemory 会议，生成周报 Markdown。

用法:
  python scripts/pull_team_week.py --start 2026-06-15 --end 2026-06-21
  python scripts/pull_team_week.py --last-week
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_io import read_json, repo_root
from unified_report import parse_vemory_meetings, parse_vertu_tasks
from vertu_client import fetch_vemory_meetings, fetch_vertu_daily_summary


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="拉取团队周报（Vertu + Vemory）")
    parser.add_argument("--start", default="", help="起始日期 YYYY-MM-DD")
    parser.add_argument("--end", default="", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--last-week", action="store_true", help="自动取上周一至周日")
    parser.add_argument("--output", default="", help="输出 Markdown 路径")
    return parser.parse_args()


def resolve_range(args: argparse.Namespace) -> tuple[str, str]:
    """解析日期区间。"""
    if args.last_week or (not args.start and not args.end):
        today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
        this_monday = today - timedelta(days=today.weekday())
        last_monday = this_monday - timedelta(days=7)
        last_sunday = this_monday - timedelta(days=1)
        return last_monday.isoformat(), last_sunday.isoformat()
    return args.start, args.end or args.start


def load_users() -> list[dict[str, Any]]:
    """读取成员 uid 映射，按 uid 去重。"""
    data = read_json(repo_root() / "config" / "odoo_user_ids.json")
    users = data.get("users") or {}
    seen_uids: set[int] = set()
    rows: list[dict[str, Any]] = []
    for username, info in users.items():
        uid = int(info.get("odoo_user_id") or 0)
        if not uid or uid in seen_uids:
            continue
        seen_uids.add(uid)
        rows.append(
            {
                "username": username,
                "odoo_user_id": uid,
                "vertu_name": str(info.get("vertu_name") or username),
            }
        )
    return sorted(rows, key=lambda item: item["username"])


def fetch_vertu_range(user_id: int, start: str, end: str) -> dict[str, Any]:
    """
    拉取日期区间 Vertu 日报。

    @param user_id Odoo uid
    @param start 起始日
    @param end 结束日
    """
    from vertu_client import run_vertu_json

    return run_vertu_json(
        [
            "odoo",
            "daily-report",
            "user-summary",
            "--user-id",
            str(user_id),
            "--start-time",
            start,
            "--end-time",
            end,
        ],
        timeout=180,
    )


def summarize_vertu_week(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    按日提取 Vertu 任务摘要。

    @param payload user-summary 响应
    @returns 每日条目
    """
    out: list[dict[str, Any]] = []
    for report in payload.get("daily_reports") or []:
        date_text = str(report.get("report_date") or report.get("date") or "")[:10]
        body = report.get("payload") or {}
        tasks = []
        for item in body.get("today") or []:
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            main = title.split("\n")[0].strip()
            tasks.append(
                {
                    "title": main,
                    "progress": int(item.get("progress") or 0),
                    "hours": float(item.get("spent_hours") or 0),
                }
            )
        if tasks or date_text:
            out.append({"date": date_text, "tasks": tasks})
    return out


def render_markdown(
    start: str,
    end: str,
    people: list[dict[str, Any]],
) -> str:
    """渲染团队周报 Markdown。"""
    lines = [
        f"# 团队工作周报 · {start} ~ {end}",
        "",
        "> 数据来源：Vertu 业务日报 + Vemory 会议（Cursor POST 库暂不可达时以业务源为准）",
        "",
    ]

    total_days = 0
    total_tasks = 0
    total_meetings = 0
    total_hours = 0.0

    for person in people:
        username = person["username"]
        name = person["vertu_name"]
        vertu_days = person.get("vertu_days") or []
        meetings = person.get("meetings") or []

        day_count = len(vertu_days)
        task_count = sum(len(d.get("tasks") or []) for d in vertu_days)
        meet_count = len(meetings)
        hours = sum(float(m.get("duration_minutes") or 0) for m in meetings) / 60.0

        total_days += day_count
        total_tasks += task_count
        total_meetings += meet_count
        total_hours += hours

        lines.append(f"## {name}（{username}）")
        lines.append("")
        lines.append(
            f"- Vertu 日报：**{day_count} 天** · 任务 **{task_count} 条**"
            f" · Vemory 会议 **{meet_count} 场**（约 **{hours:.1f}h**）"
        )
        lines.append("")

        if vertu_days:
            lines.append("### Vertu 本周任务")
            for day in vertu_days:
                d = day.get("date") or "待确认"
                lines.append(f"**{d}**")
                for task in day.get("tasks") or []:
                    lines.append(
                        f"- [{task.get('progress', 0)}%] {task.get('title', '')}"
                        + (f"（{task.get('hours')}h）" if task.get("hours") else "")
                    )
                lines.append("")
        else:
            lines.append("*本周无 Vertu 日报记录*")
            lines.append("")

        if meetings:
            lines.append("### Vemory 本周会议")
            for meet in meetings[:12]:
                title = str(meet.get("name") or meet.get("title") or "会议")
                when = str(meet.get("start_time") or "")[:10]
                mins = int(meet.get("duration_minutes") or 0)
                summary = str(meet.get("summary") or "")[:200]
                lines.append(f"- **{when}** · {title}（{mins} 分钟）")
                if summary:
                    lines.append(f"  - {summary}")
            if len(meetings) > 12:
                lines.append(f"- … 另有 {len(meetings) - 12} 场")
            lines.append("")
        else:
            lines.append("*本周无 Vemory 会议*")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.insert(
        4,
        f"**团队合计**：Vertu 有效日报 {total_days} 人天 · 任务 {total_tasks} 条 · "
        f"Vemory {total_meetings} 场（约 {total_hours:.1f}h）",
    )
    lines.insert(5, "")
    return "\n".join(lines)


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    start, end = resolve_range(args)
    users = load_users()
    results: list[dict[str, Any]] = []

    print(f"Pulling {start} ~ {end} for {len(users)} people...")
    for index, user in enumerate(users, start=1):
        uid = user["odoo_user_id"]
        print(f"[{index}/{len(users)}] {user['username']} ({user['vertu_name']}) uid={uid}")
        entry: dict[str, Any] = {**user, "vertu_days": [], "meetings": []}
        try:
            vertu = fetch_vertu_range(uid, start, end)
            entry["vertu_days"] = summarize_vertu_week(vertu)
        except Exception as exc:
            entry["vertu_error"] = str(exc)[:200]
            print(f"  vertu ERR: {exc}")
        time.sleep(1.0)
        try:
            vemory_raw = fetch_vemory_meetings(uid, start, end, max_meetings=50)
            entry["meetings"] = parse_vemory_meetings(vemory_raw).get("meetings") or []
        except Exception as exc:
            entry["vemory_error"] = str(exc)[:200]
            print(f"  vemory ERR: {exc}")
        time.sleep(1.0)
        results.append(entry)

    md = render_markdown(start, end, results)
    out_path = Path(args.output) if args.output else ROOT / ".tmp" / f"team_week_{start}_{end}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")

    json_path = out_path.with_suffix(".json")
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote: {out_path}")
    print(f"Wrote: {json_path}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
从 PostgreSQL 导出日报到 Git 仓库（主管专用）。

同事只写数据库，Frank 统一跑此脚本同步到 Git。

用法:
  python export_db_to_git.py
  python export_db_to_git.py --date 2026-06-12
  python export_db_to_git.py --date today --push
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
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from db_config import db_cursor
from git_sync import git_sync
from report_io import render_daily_markdown, repo_root, write_json, write_markdown


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="从数据库导出日报到 Git")
    parser.add_argument("--date", default="today", help="日期 YYYY-MM-DD 或 today")
    parser.add_argument("--push", action="store_true", help="导出后 git commit + push")
    parser.add_argument("--all", action="store_true", help="导出该日所有用户")
    return parser.parse_args()


def resolve_date(raw: str) -> str:
    """解析日期字符串。"""
    if raw.lower() == "today":
        return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    return raw


def fetch_daily_reports(report_date: str) -> list[dict[str, Any]]:
    """从数据库读取日报 raw_json。"""
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT raw_json
            FROM daily_reports
            WHERE report_date = %s
            ORDER BY username
            """,
            (report_date,),
        )
        rows = cur.fetchall()
    reports: list[dict[str, Any]] = []
    for (raw_json,) in rows:
        if isinstance(raw_json, dict):
            reports.append(raw_json)
        elif isinstance(raw_json, str):
            reports.append(json.loads(raw_json))
        else:
            reports.append(dict(raw_json))
    return reports


def export_report(report: dict[str, Any]) -> Path:
    """导出单份日报到 daily/ 目录。"""
    username = report["user"]
    report_date = report["date"]
    out_dir = repo_root() / "daily" / username
    json_path = out_dir / f"{report_date}.json"
    md_path = out_dir / f"{report_date}.md"
    write_json(json_path, report)
    write_markdown(md_path, render_daily_markdown(report))
    return json_path


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    report_date = resolve_date(args.date)
    reports = fetch_daily_reports(report_date)
    if not reports:
        print(f"{report_date} 数据库无日报记录。")
        return

    for report in reports:
        path = export_report(report)
        print(f"已导出: {path}")

    if args.push:
        git_sync(f"chore: export daily reports from DB {report_date}", push=True)


if __name__ == "__main__":
    main()

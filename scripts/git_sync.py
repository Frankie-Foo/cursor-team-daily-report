# -*- coding: utf-8 -*-
"""
将 daily / weekly / monthly 报告备份同步到 Git。

用法:
  python git_sync.py
  python git_sync.py --message "chore: sync monthly 2026-06"
  python git_sync.py --no-push
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

SCRIPT_DIR = __import__("pathlib").Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_io import repo_root

SYNC_DIRS = ("daily", "weekly", "monthly")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="同步日报备份到 Git")
    parser.add_argument("--message", default="", help="commit message")
    parser.add_argument("--no-push", action="store_true", help="只 commit 不 push")
    return parser.parse_args()


def collect_sync_paths() -> list[str]:
    """收集需要同步的相对路径。"""
    root = repo_root()
    paths: list[str] = []
    for folder in SYNC_DIRS:
        target = root / folder
        if not target.exists():
            continue
        for file_path in target.rglob("*"):
            if file_path.is_file() and file_path.name != ".gitkeep":
                paths.append(file_path.relative_to(root).as_posix())
    return sorted(set(paths))


def git_sync(message: str, push: bool = True) -> None:
    """提交并推送报告备份文件。"""
    root = repo_root()
    paths = collect_sync_paths()
    if not paths:
        print("没有可同步的报告文件。")
        return

    subprocess.run(["git", "add", *paths], cwd=root, check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    if not status.stdout.strip():
        print("Git 无变更，跳过 commit。")
        return

    subprocess.run(["git", "commit", "-m", message], cwd=root, check=True)
    print(f"已 commit: {message}")
    if push:
        result = subprocess.run(["git", "push"], cwd=root, capture_output=True, text=True)
        if result.returncode == 0:
            print("已 push 到远程仓库。")
        else:
            print("push 失败（本地 commit 已保留）:", result.stderr.strip() or result.stdout.strip())


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    month_label = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m")
    message = args.message.strip() or f"chore: sync reports {month_label}"
    git_sync(message, push=not args.no_push)


if __name__ == "__main__":
    main()

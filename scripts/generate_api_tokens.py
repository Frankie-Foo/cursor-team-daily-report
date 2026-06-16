# -*- coding: utf-8 -*-
"""
为团队成员生成 API Token（主管专用）。

用法:
  python generate_api_tokens.py
  python generate_api_tokens.py --regenerate Ivan April
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

ROOT = SCRIPT_DIR.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.auth import load_tokens, save_tokens
from report_io import read_json, repo_root


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="生成团队 API Token")
    parser.add_argument(
        "usernames",
        nargs="*",
        help="指定用户名；省略则为 team.json 全员",
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="强制重新生成已有 token",
    )
    return parser.parse_args()


def team_usernames() -> list[str]:
    """读取 team.json 成员名单。"""
    team_path = repo_root() / "config" / "team.json"
    data = read_json(team_path)
    return [str(m["username"]) for m in data.get("members", [])]


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    targets = args.usernames or team_usernames()
    tokens = load_tokens()

    for username in targets:
        if username in tokens and not args.regenerate:
            print(f"[skip] {username}: 已有 token（加 --regenerate 可覆盖）")
            continue
        tokens[username] = secrets.token_urlsafe(32)
        print(f"[new]  {username}: {tokens[username]}")

    path = save_tokens(tokens)
    print(f"\n已写入: {path}")
    print("请私发每位同事各自的 token，不要群发。")


if __name__ == "__main__":
    main()

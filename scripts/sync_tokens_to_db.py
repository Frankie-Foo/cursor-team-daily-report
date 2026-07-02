# -*- coding: utf-8 -*-
"""
将本地 config/api_tokens.json 同步到 PostgreSQL（服务端鉴权可读 DB）。

用法:
  python scripts/sync_tokens_to_db.py
  python scripts/sync_tokens_to_db.py --users Gary Henry
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.auth import load_tokens
from db_config import db_cursor
from report_io import read_json, repo_root

TOKEN_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS api_tokens (
    username TEXT PRIMARY KEY,
    token TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="同步 API Token 到 PostgreSQL")
    parser.add_argument(
        "--users",
        nargs="*",
        default=[],
        help="仅同步指定用户名；默认全员",
    )
    return parser.parse_args()


def ensure_token_table() -> None:
    """创建 api_tokens 表。"""
    with db_cursor() as cur:
        cur.execute(TOKEN_TABLE_DDL)


def upsert_tokens(tokens: dict[str, str]) -> int:
    """
    写入 token 表。

    @param tokens username -> token
    @returns 写入条数
    """
    count = 0
    with db_cursor() as cur:
        for username, token in tokens.items():
            cur.execute(
                """
                INSERT INTO api_tokens (username, token, updated_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (username)
                DO UPDATE SET token = EXCLUDED.token, updated_at = NOW()
                """,
                (username, token),
            )
            count += 1
    return count


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    ensure_token_table()

    all_tokens = load_tokens()
    if args.users:
        selected = {u: all_tokens[u] for u in args.users if u in all_tokens}
        missing = [u for u in args.users if u not in all_tokens]
        if missing:
            raise SystemExit(f"本地 api_tokens.json 缺少: {', '.join(missing)}")
        tokens = selected
    else:
        tokens = all_tokens

    count = upsert_tokens(tokens)
    print(f"已同步 {count} 条 token 到 PostgreSQL api_tokens 表")
    for username in sorted(tokens):
        print(f"  - {username}")


if __name__ == "__main__":
    main()

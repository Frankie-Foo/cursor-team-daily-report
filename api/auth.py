# -*- coding: utf-8 -*-
"""API Token 鉴权。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_io import repo_root


def tokens_path() -> Path:
    """返回 api_tokens.json 路径。"""
    override = os.getenv("API_TOKENS_FILE", "").strip()
    if override:
        return Path(override)
    return repo_root() / "config" / "api_tokens.json"


def load_tokens() -> dict[str, str]:
    """
    读取 username -> token 映射（DB 优先，文件兜底）。

    @returns 用户名到 token 的字典
    """
    tokens: dict[str, str] = {}

    try:
        from db_config import db_cursor

        with db_cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'api_tokens'
                """
            )
            if cur.fetchone():
                cur.execute("SELECT username, token FROM api_tokens")
                for username, token in cur.fetchall():
                    tokens[str(username)] = str(token)
    except Exception:
        pass

    path = tokens_path()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        file_tokens = data.get("tokens", data) if isinstance(data, dict) else {}
        if isinstance(file_tokens, dict):
            for username, token in file_tokens.items():
                tokens.setdefault(str(username), str(token))

    return tokens


def token_to_username(token: str) -> str | None:
    """
    根据 token 解析用户名。

    @param token API Token
    @returns 用户名，无效则 None
    """
    token = token.strip()
    if not token:
        return None
    for username, stored in load_tokens().items():
        if stored == token:
            return username
    return None


def save_tokens(tokens: dict[str, str]) -> Path:
    """
    保存 token 映射。

    @param tokens username -> token
    @returns 写入路径
    """
    path = tokens_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"tokens": tokens}
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path

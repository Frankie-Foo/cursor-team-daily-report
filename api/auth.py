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
    读取 username -> token 映射。

    @returns 用户名到 token 的字典
    """
    path = tokens_path()
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "tokens" in data:
        return {str(k): str(v) for k, v in data["tokens"].items()}
    return {str(k): str(v) for k, v in data.items()}


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

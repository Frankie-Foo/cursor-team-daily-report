# -*- coding: utf-8 -*-
"""
提交已整理好的日报 JSON（同事 Skill 第 3 步：POST）。

用法:
  python submit_report.py --file .tmp/draft.json
  python submit_report.py --stdin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.schemas import prepare_report_payload
from api_client import submit_daily_via_api
from report_io import read_json


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="POST 已整理的日报到团队 API")
    parser.add_argument("--file", default="", help="日报 JSON 文件路径")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读取 JSON")
    return parser.parse_args()


def load_report(args: argparse.Namespace) -> dict[str, Any]:
    """加载日报 JSON。"""
    if args.stdin:
        return json.loads(sys.stdin.read())
    if args.file:
        return read_json(Path(args.file))
    raise ValueError("请指定 --file 或 --stdin")


def main() -> None:
    """脚本入口。"""
    args = parse_args()
    raw = load_report(args)
    payload = prepare_report_payload(raw)
    response = submit_daily_via_api(payload)
    print(
        json.dumps(
            {
                "submitted": True,
                "via": "api",
                "user": payload["user"],
                "date": payload["date"],
                "api": response,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

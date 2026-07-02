# -*- coding: utf-8 -*-
"""
通过 res.users.login 解析 odoo_user_id（绕过 name search 的 OrderedSet bug）。

用法:
  python scripts/lookup_odoo_uids.py
  python scripts/lookup_odoo_uids.py --merge
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_io import read_json, repo_root
from vertu_client import run_vertu_json

# username -> login 搜索片段（按 Vertu 邮箱习惯）
LOGIN_PATTERNS: dict[str, list[str]] = {
    "Sam": ["sam@", "sam."],
    "Gary": ["gary@"],
    "May": ["may@", "may."],
    "Lina": ["lina@", "lina.", "lina@vertu.cn"],
    "April": ["april@", "april."],
    "Ivan": ["ivan@", "ivan."],
    "Viki": ["viki@", "viki."],
    "Vivi": ["vivi@", "vivi."],
    "Chris": ["chris@", "christina@", "chris."],
    "Safae": ["safae@", "safae."],
    "Miranda": ["miranda@", "miranda."],
}


def search_users_by_login(pattern: str) -> list[dict]:
    """
    按 login 模糊查 res.users。

    @param pattern ilike 片段
    @returns 用户行
    """
    domain_path = ROOT / ".tmp" / "login_domain.json"
    domain_path.parent.mkdir(parents=True, exist_ok=True)
    domain_path.write_text(
        json.dumps([["login", "ilike", pattern]], ensure_ascii=False),
        encoding="utf-8",
    )
    payload = run_vertu_json(
        [
            "odoo",
            "data",
            "search",
            "res.users",
            "--fields",
            "id,name,login,email",
            "--domain",
            f"@{domain_path}",
            "--limit",
            "15",
        ],
        timeout=90,
    )
    if isinstance(payload, list):
        return payload
    return payload.get("result") or []


def pick_best(username: str, rows: list[dict]) -> dict | None:
    """
    在多个 login 命中时选最像内部员工的账号。

    @param username 团队英文名
    @param rows 候选
    @returns 最佳行或 None
    """
    if not rows:
        return None
    if len(rows) == 1:
        return rows[0]

    vertu_rows = [r for r in rows if str(r.get("login") or "").endswith("@vertu.cn")]
    pool = vertu_rows or rows

    # Vivi：优先 vivi.li@
    if username == "Vivi":
        for row in pool:
            login = str(row.get("login") or "").lower()
            if login.startswith("vivi.li@"):
                return row

    # Chris：优先 chris.wu@
    if username == "Chris":
        for row in pool:
            login = str(row.get("login") or "").lower()
            if login.startswith("chris.wu@"):
                return row

    return pool[0]


def main() -> None:
    """脚本入口。"""
    parser = argparse.ArgumentParser(description="按 login 查 odoo_user_id")
    parser.add_argument("--merge", action="store_true", help="写入 config/odoo_user_ids.json")
    args = parser.parse_args()

    results: list[dict] = []
    print("| username | uid | login | vertu_name |")
    print("|----------|-----|-------|------------|")

    for username, patterns in LOGIN_PATTERNS.items():
        candidates: dict[int, dict] = {}
        for pattern in patterns:
            try:
                for row in search_users_by_login(pattern):
                    candidates[int(row["id"])] = row
            except RuntimeError as exc:
                print(f"# {username}/{pattern}: {exc}", file=sys.stderr)
            time.sleep(1.2)

        rows = list(candidates.values())
        best = pick_best(username, rows)
        uid = int(best["id"]) if best else None
        vertu_name = str(best.get("name") or "") if best else ""
        login = str(best.get("login") or "") if best else ""
        note = ""
        if len(rows) > 1 and best:
            note = f" (从 {len(rows)} 个候选中选取)"
        print(f"| {username} | {uid or '待确认'} | {login or '-'} | {vertu_name or '-'} |{note}")
        results.append(
            {
                "username": username,
                "odoo_user_id": uid,
                "vertu_name": vertu_name,
                "login": login,
                "candidates": [
                    {"id": r["id"], "name": r.get("name"), "login": r.get("login")}
                    for r in rows
                ],
            }
        )

    out_path = ROOT / "config" / "_uid_login_lookup.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n详细结果 -> {out_path}")

    if args.merge:
        uid_path = repo_root() / "config" / "odoo_user_ids.json"
        data = read_json(uid_path)
        users = data.setdefault("users", {})
        merged: list[str] = []
        for row in results:
            if not row["odoo_user_id"]:
                continue
            entry = users.setdefault(row["username"], {})
            if not entry.get("odoo_user_id"):
                entry["odoo_user_id"] = row["odoo_user_id"]
                entry["vertu_name"] = row["vertu_name"]
                merged.append(row["username"])
        uid_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("已合并到 odoo_user_ids.json:", ", ".join(merged) if merged else "无")


if __name__ == "__main__":
    main()

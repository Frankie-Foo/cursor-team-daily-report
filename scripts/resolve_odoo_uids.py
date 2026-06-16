# -*- coding: utf-8 -*-
"""
从 Vertu 可访问数据源解析 odoo_user_id（绕过 res.users search 服务端 bug）。

优先级：
  1. config/odoo_user_ids.json 手工映射
  2. wechat.checkin.daily.report.compare 日报比对表（Frank 可见范围内）
  3. vertu odoo me（仅当前登录用户）

用法:
  python scripts/resolve_odoo_uids.py
  python scripts/resolve_odoo_uids.py --merge-into config/odoo_user_ids.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_io import read_json, repo_root
from vertu_client import run_vertu_json

# username -> 可能出现在 Vertu 的中文名 / 英文名
NAME_HINTS: dict[str, list[str]] = {
    "Frank": ["刘春梅", "Frank"],
    "Haiwen": ["何海文", "Haiwen"],
    "Qiqi": ["张琪", "Qiqi"],
    "Xianna": ["鲜娜", "Xianna"],
    "Zhangyi": ["张懿", "Zhangyi"],
    "Yubing": ["于冰", "Yubing"],
    "Sam": ["Sam"],
    "Gary": ["Gary"],
    "May": ["May"],
    "Lina": ["Lina", "丽娜"],
    "April": ["April"],
    "Ivan": ["Ivan"],
    "Viki": ["Viki"],
    "Vivi": ["Vivi"],
    "Chris": ["Chris"],
}


def load_manual_map() -> dict[str, dict]:
    """读取手工 uid 映射。"""
    path = repo_root() / "config" / "odoo_user_ids.json"
    if not path.exists():
        return {}
    return read_json(path).get("users") or {}


def fetch_compare_roster(dates: list[str], limit: int = 200) -> list[dict]:
    """
    从日报比对表拉取 user_id / 姓名 / 部门（res.users search 的替代方案）。

    @param dates YYYY-MM-DD 列表
    @returns [{user_id, user_name, department_name}]
    """
    seen: dict[int, dict] = {}
    for date_text in dates:
        domain = json.dumps([("compare_date", "=", date_text)])
        try:
            payload = run_vertu_json(
                [
                    "odoo",
                    "data",
                    "search",
                    "wechat.checkin.daily.report.compare",
                    "--fields",
                    "user_id,user_name,department_name",
                    "--domain",
                    domain,
                    "--limit",
                    str(limit),
                ],
                timeout=120,
            )
        except RuntimeError as exc:
            print(f"  skip {date_text}: {exc}", file=sys.stderr)
            continue

        rows = payload if isinstance(payload, list) else payload.get("result") or []
        for row in rows:
            uid_field = row.get("user_id")
            if not (isinstance(uid_field, list) and uid_field):
                continue
            uid = int(uid_field[0])
            name = str(uid_field[1] if len(uid_field) > 1 else row.get("user_name") or "")
            dept = str(row.get("department_name") or "")
            if uid not in seen:
                seen[uid] = {
                    "user_id": uid,
                    "user_name": name,
                    "department_name": dept,
                }
        time.sleep(1.5)

    return sorted(seen.values(), key=lambda item: (item["department_name"], item["user_name"]))


def match_username(username: str, display: str, roster: list[dict]) -> tuple[int | None, str, str]:
    """
    在 roster 中按 hints 模糊匹配 uid。

    @returns (uid, matched_name, department)
    """
    hints = [h.lower() for h in NAME_HINTS.get(username, [display, username]) if h]
    for item in roster:
        name = str(item.get("user_name") or "")
        dept = str(item.get("department_name") or "")
        name_lower = name.lower()
        for hint in hints:
            if hint and (hint in name_lower or hint in name or hint in dept.lower()):
                return int(item["user_id"]), name, dept
    return None, "", ""


def fetch_current_user_me() -> dict | None:
    """拉取当前 vertu 登录用户的 me 信息。"""
    try:
        payload = run_vertu_json(["odoo", "me"], timeout=60)
    except RuntimeError:
        return None
    if isinstance(payload, dict) and payload.get("user_id"):
        return payload
    return None


def main() -> None:
    """脚本入口。"""
    parser = argparse.ArgumentParser(description="解析团队 odoo_user_id")
    parser.add_argument(
        "--merge-into",
        default="",
        help="将自动匹配结果合并写回 odoo_user_ids.json（仅填充仍为 null 的项）",
    )
    parser.add_argument(
        "--dates",
        default="2026-06-09,2026-06-10,2026-06-11,2026-06-12",
        help="compare 表查询日期，逗号分隔",
    )
    args = parser.parse_args()

    team = read_json(repo_root() / "config" / "team.json")
    manual = load_manual_map()
    dates = [d.strip() for d in args.dates.split(",") if d.strip()]

    print("拉取 compare 表 roster（替代 res.users search）...")
    roster = fetch_compare_roster(dates)
    probe_path = repo_root() / "config" / "_uid_roster_probe.json"
    probe_path.write_text(json.dumps(roster, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  可见 {len(roster)} 人 -> {probe_path}")

    me = fetch_current_user_me()
    if me:
        print(f"  当前登录: {me.get('name')} uid={me.get('user_id')}")

    results: list[dict] = []
    for member in team.get("members", []):
        username = str(member.get("username") or "")
        display = str(member.get("display_name") or username)
        manual_entry = manual.get(username) or {}
        uid = manual_entry.get("odoo_user_id")
        vertu_name = str(manual_entry.get("vertu_name") or "")
        source = "manual" if uid else "missing"

        if not uid:
            found_uid, matched, dept = match_username(username, display, roster)
            if found_uid:
                uid, vertu_name, source = found_uid, matched, "compare"

        if not uid and me and username == "Frank":
            uid = int(me["user_id"])
            vertu_name = str(me.get("name") or vertu_name)
            source = "me"

        results.append(
            {
                "username": username,
                "display_name": display,
                "odoo_user_id": uid,
                "vertu_name": vertu_name,
                "source": source,
            }
        )

    print("\n| username | uid | source | vertu_name |")
    print("|----------|-----|--------|------------|")
    for row in results:
        uid = row["odoo_user_id"] or "待确认"
        print(f"| {row['username']} | {uid} | {row['source']} | {row['vertu_name'] or '-'} |")

    missing = [r["username"] for r in results if not r["odoo_user_id"]]
    if missing:
        print("\n仍待确认:", ", ".join(missing))
        print("请同事各自运行: powershell -File scripts/collect_my_odoo_uid.ps1")
        print("把输出的 uid 填入 config/odoo_user_ids.json 后重新 export。")

    if args.merge_into:
        out_path = repo_root() / args.merge_into
        data = read_json(out_path) if out_path.exists() else {"users": {}}
        users = data.setdefault("users", {})
        for row in results:
            username = row["username"]
            if not row["odoo_user_id"]:
                continue
            entry = users.setdefault(username, {})
            if not entry.get("odoo_user_id"):
                entry["odoo_user_id"] = row["odoo_user_id"]
            if row["vertu_name"] and not entry.get("vertu_name"):
                entry["vertu_name"] = row["vertu_name"]
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n已合并 -> {out_path}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""用 vertu / vertu-cli 批量解析 9 人 odoo_user_id。"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_io import read_json, repo_root
from vertu_client import run_vertu_json

TARGETS = ["Sam", "Gary", "May", "Lina", "April", "Ivan", "Viki", "Vivi", "Chris"]

# 英文名 + 可能中文名/别名（compare / 口头称呼）
SEARCH_HINTS: dict[str, list[str]] = {
    "Sam": ["Sam", "山姆", "萨姆"],
    "Gary": ["Gary", "盖瑞"],
    "May": ["May", "梅", "杨May"],
    "Lina": ["Lina", "丽娜", "李"],
    "April": ["April", "艾"],
    "Ivan": ["Ivan", "伊凡", "兵"],
    "Viki": ["Viki", "维琪"],
    "Vivi": ["Vivi", "薇薇"],
    "Chris": ["Chris", "克里斯", "Chrismy"],
}


def search_compare(date_text: str, keyword: str) -> list[dict]:
    """
    在日报 compare 表按 user_name 模糊查 uid。

    @param date_text YYYY-MM-DD
    @param keyword 姓名片段
    @returns 行列表
    """
    domain_path = ROOT / ".tmp" / "compare_domain.json"
    domain_path.parent.mkdir(parents=True, exist_ok=True)
    domain_path.write_text(
        json.dumps(
            [
                ["compare_date", "=", date_text],
                ["user_name", "ilike", keyword],
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    payload = run_vertu_json(
        [
            "odoo",
            "data",
            "search",
            "wechat.checkin.daily.report.compare",
            "--fields",
            "user_id,user_name,department_name",
            "--domain",
            f"@{domain_path}",
            "--limit",
            "20",
        ],
        timeout=120,
    )
    if isinstance(payload, list):
        return payload
    return payload.get("result") or []


def read_user(uid: int) -> dict | None:
    """按 id 读取 res.users（绕过 search bug）。"""
    try:
        payload = run_vertu_json(
            [
                "odoo",
                "data",
                "read",
                "res.users",
                str(uid),
                "--fields",
                "id,name,login,email",
            ],
            timeout=60,
        )
    except RuntimeError:
        return None
    if isinstance(payload, list) and payload:
        return payload[0]
    if isinstance(payload, dict) and payload.get("id"):
        return payload
    if isinstance(payload, dict):
        rows = payload.get("result") or []
        return rows[0] if rows else None
    return None


def run_vertu_cli_me() -> dict | None:
    """vertu-cli hr +me（legacy Odoo）。"""
    npm = Path.home() / "AppData" / "Roaming" / "npm" / "vertu-cli.cmd"
    if not npm.exists():
        return None
    proc = subprocess.run(
        [str(npm), "--base-url", "https://admin.vertu.cn", "hr", "+me"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def main() -> None:
    """脚本入口。"""
    dates = [f"2026-06-{day:02d}" for day in range(9, 16)]
    hits: dict[str, list[dict]] = {name: [] for name in TARGETS}
    seen: set[tuple[int, str]] = set()

    print("1) compare 表按姓名片段搜索...")
    for name in TARGETS:
        for hint in SEARCH_HINTS.get(name, [name]):
            for date_text in dates:
                try:
                    rows = search_compare(date_text, hint)
                except RuntimeError as exc:
                    msg = str(exc).encode("unicode_escape").decode("ascii")[:120]
                    print(f"  skip {name}/{hint}/{date_text}: {msg}")
                    time.sleep(3)
                    continue
                for row in rows:
                    uid_field = row.get("user_id")
                    if not (isinstance(uid_field, list) and uid_field):
                        continue
                    uid = int(uid_field[0])
                    uname = str(uid_field[1] if len(uid_field) > 1 else row.get("user_name") or "")
                    key = (uid, uname)
                    if key in seen:
                        continue
                    seen.add(key)
                    hits[name].append(
                        {
                            "odoo_user_id": uid,
                            "user_name": uname,
                            "department_name": str(row.get("department_name") or ""),
                            "hint": hint,
                            "date": date_text,
                            "source": "compare",
                        }
                    )
                time.sleep(1.5)

    print("2) 读取 compare roster 全量名单...")
    roster_path = repo_root() / "config" / "_uid_roster_probe.json"
    if roster_path.exists():
        roster = read_json(roster_path)
        for name in TARGETS:
            hints = [h.lower() for h in SEARCH_HINTS.get(name, [name]) if h]
            for item in roster:
                uname = str(item.get("user_name") or "")
                dept = str(item.get("department_name") or "")
                blob = f"{uname} {dept}".lower()
                if any(h in blob or h in uname.lower() for h in hints):
                    uid = int(item["user_id"])
                    key = (uid, uname)
                    if key not in seen:
                        seen.add(key)
                        hits[name].append(
                            {
                                "odoo_user_id": uid,
                                "user_name": uname,
                                "department_name": dept,
                                "hint": "roster",
                                "date": "",
                                "source": "roster",
                            }
                        )

    out_probe = repo_root() / "config" / "_uid_batch_hits.json"
    out_probe.write_text(json.dumps(hits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  -> {out_probe}")

    # 合并到 odoo_user_ids.json（仅唯一匹配时自动填）
    uid_path = repo_root() / "config" / "odoo_user_ids.json"
    data = read_json(uid_path)
    users = data.setdefault("users", {})
    merged: list[str] = []

    print("\n| username | 候选数 | 自动填入 | 候选 |")
    print("|----------|--------|----------|------|")
    for name in TARGETS:
        candidates = hits.get(name) or []
        auto_uid = None
        auto_name = ""
        if len(candidates) == 1:
            auto_uid = candidates[0]["odoo_user_id"]
            auto_name = candidates[0]["user_name"]
            entry = users.setdefault(name, {})
            if not entry.get("odoo_user_id"):
                entry["odoo_user_id"] = auto_uid
                entry["vertu_name"] = auto_name
                merged.append(name)
        cand_text = "; ".join(
            f"{c['odoo_user_id']}:{c['user_name']}" for c in candidates[:3]
        ) or "-"
        fill = str(auto_uid) if auto_uid else ("待确认" if candidates else "无命中")
        print(f"| {name} | {len(candidates)} | {fill} | {cand_text} |")

    uid_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if merged:
        print("\n已自动合并:", ", ".join(merged))
    else:
        print("\n无唯一匹配，未自动写入 odoo_user_ids.json")

    me = run_vertu_cli_me()
    if me:
        print(f"\nvertu-cli +me: {me.get('name')} uid={me.get('user_id')}")


if __name__ == "__main__":
    main()

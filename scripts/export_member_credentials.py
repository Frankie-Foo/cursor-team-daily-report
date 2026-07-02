# -*- coding: utf-8 -*-
"""
合并 team.json + api_tokens.json + odoo_user_ids.json，生成同事私发配置表。

用法:
  python scripts/export_member_credentials.py
  python scripts/export_member_credentials.py --try-vertu   # Vertu 自动查 uid（当前服务端可能失败）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from report_io import get_api_url, read_json, repo_root

# 手工补充：Vertu 中文名 / 别名 -> username（compare 表模糊匹配时使用）
DISPLAY_ALIASES: dict[str, list[str]] = {
    "Yubing": ["于冰"],
    "Haiwen": ["何海文"],
    "Xianna": ["鲜娜", "Xianna"],
    "Qiqi": ["张琪", "Qiqi"],
    "Zhangyi": ["张懿", "Zhangyi"],
    "Frank": ["Frank", "刘春梅"],
    "Lina": ["Lina", "DEHDAHOUMAIMA", "1176", "lina@vertu.cn"],
    "May": ["May", "刘春梅"],
    "April": ["April", "杨晶晶"],
    "Ivan": ["Ivan", "于冰"],
    "Viki": ["Viki"],
    "Vivi": ["Vivi", "王宇彤", "3568"],
    "Chris": ["Chris", "冯磊", "冯磊-1", "2341"],
    "Henry": ["Henry", "李浩然", "henry.li@vertu.cn"],
    "Safae": ["Safae", "Safae Ben M'hamed", "safae@vertu.cn"],
    "Miranda": ["Miranda", "刘雪梅", "miranda.liu@vertu.cn"],
    "Sam": ["Sam"],
    "Gary": ["Gary"],
    "May": ["May"],
}


def load_odoo_user_map() -> dict[str, dict]:
    """
    读取手工维护的 Odoo uid 映射。

    @returns username -> {odoo_user_id, vertu_name}
    """
    path = repo_root() / "config" / "odoo_user_ids.json"
    if not path.exists():
        example = repo_root() / "config" / "odoo_user_ids.example.json"
        if example.exists():
            print(f"提示: 复制 {example.name} 为 odoo_user_ids.json 并填写 uid")
        return {}
    data = read_json(path)
    return data.get("users") or {}


def search_user_id(keywords: list[str]) -> tuple[int | None, str]:
    """
    在 Vertu 中按名字搜索 user id（服务端 bug 时可能全部失败）。

    @param keywords 搜索关键词列表
    @returns (user_id, matched_name)
    """
    from vertu_client import run_vertu_json

    for keyword in keywords:
        if not keyword:
            continue
        domain = json.dumps([("name", "ilike", keyword)])
        try:
            payload = run_vertu_json(
                [
                    "odoo",
                    "data",
                    "search",
                    "res.users",
                    "--fields",
                    "id,name,login",
                    "--domain",
                    domain,
                    "--limit",
                    "5",
                ]
            )
        except RuntimeError:
            continue
        rows = payload.get("result") or payload.get("records") or []
        if isinstance(payload, list):
            rows = payload
        for row in rows:
            name = str(row.get("name") or "")
            uid = int(row.get("id") or 0)
            if uid and (keyword.lower() in name.lower() or keyword in name):
                return uid, name
        if rows:
            row = rows[0]
            return int(row.get("id") or 0) or None, str(row.get("name") or "")
    return None, ""


def resolve_member_uid(
    username: str,
    display: str,
    manual_map: dict[str, dict],
    try_vertu: bool,
) -> tuple[int | None, str, str]:
    """
    解析成员的 odoo_user_id。

    @returns (uid, vertu_name, source)
    """
    manual = manual_map.get(username) or {}
    uid = manual.get("odoo_user_id")
    vertu_name = str(manual.get("vertu_name") or "")
    if uid:
        return int(uid), vertu_name, "manual"

    if try_vertu:
        keywords = list(dict.fromkeys([display, username, *DISPLAY_ALIASES.get(username, [])]))
        found_uid, matched = search_user_id(keywords)
        if found_uid:
            return found_uid, matched, "vertu"

    return None, vertu_name, "missing"


def build_private_message(member: dict) -> str:
    """生成可直接微信私发的话术。"""
    uid = member["odoo_user_id"] if member["odoo_user_id"] else "待确认"
    return "\n".join(
        [
            "【Cursor 日报安装】",
            f"API 地址：{member['report_api_url']}",
            f"username：{member['username']}",
            f"display_name：{member['display_name']}",
            f"odoo_user_id：{uid}",
            f"API Token：{member['api_token']}",
            "",
            "解压 zip 后双击 SETUP.bat，按提示填 Cursor 项目路径即可。",
        ]
    )


def main() -> None:
    """脚本入口。"""
    parser = argparse.ArgumentParser(description="导出同事私发配置表")
    parser.add_argument(
        "--try-vertu",
        action="store_true",
        help="Vertu res.users 自动查 uid（当前服务端可能报错，默认用手工映射）",
    )
    args = parser.parse_args()

    team_path = repo_root() / "config" / "team.json"
    tokens_path = repo_root() / "config" / "api_tokens.json"
    team = read_json(team_path)
    tokens = read_json(tokens_path).get("tokens", {})
    manual_map = load_odoo_user_map()
    try:
        report_api_url = get_api_url().rstrip("/")
    except ValueError:
        report_api_url = "https://YOUR-PUBLIC-API-URL"

    members_out: list[dict] = []
    seen: set[str] = set()

    for member in team.get("members", []):
        username = str(member.get("username") or "")
        display = str(member.get("display_name") or username)
        token = tokens.get(username, "")
        uid, vertu_name, source = resolve_member_uid(username, display, manual_map, args.try_vertu)
        seen.add(username)
        members_out.append(
            {
                "username": username,
                "display_name": display,
                "odoo_user_id": uid,
                "vertu_matched_name": vertu_name,
                "uid_source": source,
                "api_token": token,
                "report_api_url": report_api_url,
            }
        )

    # api_tokens 里有、team.json 里没有的人（如 Yubing）
    for username, token in tokens.items():
        if username in seen:
            continue
        display = manual_map.get(username, {}).get("vertu_name") or username
        uid, vertu_name, source = resolve_member_uid(username, display, manual_map, args.try_vertu)
        members_out.append(
            {
                "username": username,
                "display_name": display if display != username else username,
                "odoo_user_id": uid,
                "vertu_matched_name": vertu_name,
                "uid_source": source,
                "api_token": token,
                "report_api_url": report_api_url,
            }
        )

    out_json = repo_root() / "config" / "member_credentials.json"
    out_md = repo_root() / "config" / "member_credentials.md"
    export_payload = {
        "report_api_url": report_api_url,
        "members": [{k: v for k, v in m.items() if k != "uid_source"} for m in members_out],
    }
    out_json.write_text(
        json.dumps(export_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# 同事私发配置表（勿群发、勿提交 Git）",
        "",
        f"API 地址：`{report_api_url}`",
        "",
        "维护 uid：编辑 `config/odoo_user_ids.json` 后重新运行 `python scripts/export_member_credentials.py`",
        "",
        "## 汇总表",
        "",
        "| username | 展示名 | odoo_user_id | Vertu名 | API Token |",
        "|----------|--------|--------------|---------|-----------|",
    ]
    for m in members_out:
        uid = m["odoo_user_id"] if m["odoo_user_id"] else "**待确认**"
        vertu = m["vertu_matched_name"] or "-"
        lines.append(
            f"| {m['username']} | {m['display_name']} | {uid} | {vertu} | `{m['api_token']}` |"
        )

    lines.extend(["", "## 逐人私发话术", ""])
    for m in members_out:
        lines.extend(
            [
                f"### {m['username']}（{m['display_name']}）",
                "",
                "```",
                build_private_message(m),
                "```",
                "",
            ]
        )

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print(f"JSON: {out_json}")
    print(f"MD:   {out_md}")
    missing = [m["username"] for m in members_out if not m["odoo_user_id"]]
    if missing:
        print("待确认 odoo_user_id:", ", ".join(missing))
        print("请在 config/odoo_user_ids.json 填写后重新运行本脚本。")


if __name__ == "__main__":
    main()

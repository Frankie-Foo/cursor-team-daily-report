# -*- coding: utf-8 -*-
r"""Generate one-paste setup prompts for each active team member.

Each prompt pasted into Cursor Agent chat will auto-configure:
1. pip dependencies
2. Download scripts (report_io.py, publish_daily.py, etc.)
3. Write .env + config/user.json
4. Create Cursor Automation (workday 17:30 auto-submit)
5. Test run

Output: outbox/oneclick-setup/<username>-一键安装.txt
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outbox" / "oneclick-setup"

API_URL = "https://global-pdca.vertu.cn"
RAW_BASE = "https://raw.githubusercontent.com/Frankie-Foo/cursor-team-daily-report/main/scripts"

# --- 每个人粘贴这一整段即可 --- #
TEMPLATE = r"""帮我配置日报自动化，往下按步骤执行不要跳过：

## 1 检查环境
终端执行: python --version
要求 >= 3.10，没有就去 https://www.python.org/downloads/ 装。
终端执行: pip install requests python-dotenv --quiet

## 2 创建目录
终端执行: mkdir %USERPROFILE%\.cursor\daily-report\config -Force
终端执行: mkdir %USERPROFILE%\.cursor\daily-report\scripts -Force

## 3 下载脚本（用 Write 工具写入，不要用 Invoke-WebRequest）
用 Write 工具写入以下文件：

### {raw}/report_io.py → %USERPROFILE%\.cursor\daily-report\scripts\report_io.py
### {raw}/publish_daily.py → %USERPROFILE%\.cursor\daily-report\scripts\publish_daily.py
### {raw}/api_client.py → %USERPROFILE%\.cursor\daily-report\scripts\api_client.py
### {raw}/parse_transcripts.py → %USERPROFILE%\.cursor\daily-report\scripts\parse_transcripts.py

## 4 写入 .env

用 Write 工具写入 %USERPROFILE%\.cursor\daily-report\.env，内容：

REPORT_API_URL={api_url}
REPORT_API_TOKEN={token}
CURSOR_REPORT_USER={username}

## 5 写入 user.json

用 Write 工具写入 %USERPROFILE%\.cursor\daily-report\config\user.json，内容：

{{
  "username": "{username}",
  "timezone": "Asia/Shanghai",
  "cursor_workspace": "请替换为你的 Cursor 项目路径，反斜杠改正斜杠",
  "odoo_user_id": 0
}}

然后把 cursor_workspace 改成你实际的 Cursor 项目根目录。

## 6 创建 Automation

用 Write 工具写入 %USERPROFILE%\.cursor\automations\daily-report-submit.md：

---
schedule: "30 9 * * 1-5"
description: "Workday 17:30 auto-submit Cursor daily report"
---
执行以下命令提交今天的日报：

cd $env:USERPROFILE\.cursor\daily-report
python scripts/publish_daily.py --date today --api-only

输出必须包含 "submitted": true, "via": "api"，否则在消息中报告错误。

## 7 试跑
终端执行: cd %USERPROFILE%\.cursor\daily-report && python scripts/publish_daily.py --date today --api-only
成功后输出 should include: submitted true via api

全部完成后告诉我「配置完成，每天 17:30 自动提交」。"""  # noqa: E501


def main() -> None:
    """Generate one setup prompt per active team member."""
    team_path = ROOT / "config" / "team.json"
    creds_path = ROOT / "config" / "member_credentials.json"

    if not team_path.exists():
        sys.exit("team.json not found")
    if not creds_path.exists():
        sys.exit("member_credentials.json not found")

    team = json.loads(team_path.read_text(encoding="utf-8"))
    creds = json.loads(creds_path.read_text(encoding="utf-8"))

    active = {m["username"] for m in team["members"] if not m.get("skip_report")}
    creds_map = {
        m["username"]: m.get("api_token", "")
        for m in creds["members"]
    }

    OUT.mkdir(parents=True, exist_ok=True)

    for username in sorted(active):
        token = creds_map.get(username, "")
        if not token:
            print(f"SKIP {username}: no token")
            continue

        content = TEMPLATE.format(
            username=username,
            token=token,
            api_url=API_URL,
            raw=RAW_BASE,
        )

        out_file = OUT / f"{username}-一键安装.txt"
        out_file.write_text(content, encoding="utf-8")
        print(f"OK  {username} → {out_file.name}")

    print(f"\nDone. {OUT}")
    print("复制 .txt 全部内容，粘贴到对应人的 Cursor Agent 聊天框。Agent 会按 7 步执行。")
    print()
    print("第 5 步的 cursor_workspace 需要每个人手动改一次（改为自己的项目路径）。")
    print("其余全自动，不需要管理员权限。")


if __name__ == "__main__":
    main()

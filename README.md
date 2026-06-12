# Cursor 团队日报系统

10 人团队 Cursor 工作日报：解析 agent-transcripts → PostgreSQL → Git 备份。

## 快速开始

```powershell
pip install -r requirements.txt
copy .env.example .env          # 填 DB 密码
copy config\user.example.json config\user.json   # 填你的 username
python scripts/db_schema.py --create-db
python scripts/publish_daily.py --date today --workspace "D:/你的Cursor项目路径"
powershell -ExecutionPolicy Bypass -File scripts/install_skill.ps1
```

## 常用命令

```bash
python scripts/publish_daily.py --date today --git-push
python scripts/query_team.py --scope
python scripts/query_team.py --status
python scripts/git_sync.py
```

## 目录

| 路径 | 说明 |
|------|------|
| `config/team.json` | 全员名单 |
| `config/org.json` | 总监 / 小组长权限 |
| `scripts/` | 解析、入库、查询、Git 同步 |
| `daily/` `weekly/` `monthly/` | 报告 Git 备份 |
| `.cursor/skills/` | Cursor Skill |

## 部署给成员

1. `git clone` 本仓库
2. 运行 `scripts/setup.ps1`
3. 配置 `config/user.json`（username 与 team.json 一致）
4. 安装 Skill + 配置 Automation（见 `automation/cursor-daily-report.md`）

`.env` 和 `config/user.json` 不入 Git。

# Cursor 团队日报系统

仓库：https://github.com/Frankie-Foo/cursor-team-daily-report

## 发给成员

请直接把 **[docs/成员部署指南.md](docs/成员部署指南.md)** 发给团队，按文档操作即可。

## 主管快速命令

```powershell
# 今天全员提交状态
python scripts/query_team.py --status

# 发布自己的日报
python scripts/publish_today.ps1
```

## 目录

| 路径 | 说明 |
|------|------|
| `docs/成员部署指南.md` | **发给成员的小白文档** |
| `.cursor/skills/cursor-daily-report/` | Cursor Skill |
| `config/team.json` | 14 人名单 |
| `config/org.json` | 总监/组长权限 |
| `scripts/` | 全部脚本 |

`.env` 和 `config/user.json` 不入 Git。

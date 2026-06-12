# Cursor Automation — 团队日报

## 定时配置

| 字段 | 值 |
|------|-----|
| 名称 | Cursor 团队日报 |
| Cron | `30 17 * * 1-5` |
| 时区 | Asia/Shanghai |
| Skill | `cursor-daily-report` |

## Prompt（复制到 Automation）

```text
运行 cursor-daily-report skill，完成今日日报：
1. 从 config/user.json 读取 username 和 cursor_workspace
2. 解析今天 agent-transcripts 并精炼 daily_summary（详细版中文摘要）
3. 执行 python scripts/publish_daily.py --date today --git-push
4. 汇报会话数、文件路径、是否成功入库和 push
若今天无会话，仍发布空日报。
```

## 主管定时任务（可选）

| 任务 | Cron | 命令 |
|------|------|------|
| 周报 | `0 18 * * 5` | `scripts/run_weekly.ps1` |
| 月报 | `0 9 1 * *` | `scripts/run_monthly.ps1` |

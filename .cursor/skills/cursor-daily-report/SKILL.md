---
name: cursor-daily-report
description: >-
  生成并发布 Cursor 团队日报：解析 agent-transcripts、写入 PostgreSQL、可选 Git 同步。
  Use when user asks for daily cursor report, team activity summary, end-of-day
  cursor summary, or when scheduled automation runs the daily report workflow.
---

# Cursor 团队日报 Skill

## 角色区分

| 角色 | 发布命令 |
|------|----------|
| **同事** | `python scripts/publish_daily.py --date today --db-only` |
| **主管 (Frank)** | `python scripts/publish_daily.py --date today --git-push` 或定时 `export_db_to_git.py --push` |

同事只写数据库；Git 由主管从 DB 导出后统一 push。详见 `docs/主管Git同步指南.md`。

## 适用场景

- 用户说：「发今日日报」「运行 cursor daily report」「总结今天 Cursor 做了什么」
- Cursor Automation 工作日 17:30 定时触发

## 前置检查

执行前确认仓库/Skill 根目录存在：

- `config/user.json` — 含 `username`、`cursor_workspace`
- `.env` — 含数据库连接信息

读取配置：

```bash
python -c "import sys; sys.path.insert(0,'scripts'); from report_io import get_username, get_cursor_workspace; print(get_username(), get_cursor_workspace())"
```

## 标准工作流（按顺序）

```
- [ ] 1. 解析今日 transcripts
- [ ] 2. AI 精炼 daily_summary（详细版，中文，3-6 条）
- [ ] 3. 发布：同事 --db-only / 主管 --git-push
- [ ] 4. 回报结果
```

### Step 1：解析

```bash
python scripts/parse_transcripts.py --date today --workspace "<cursor_workspace>" --output .tmp/parsed.json
```

`cursor_workspace` 从 `config/user.json` 读取，**不是**本日报仓库路径。

### Step 2：AI 精炼 daily_summary

读取 `.tmp/parsed.json`，重写 `daily_summary`：

- 中文，面向主管
- 3-6 条 bullet
- 每条含：任务、工具、进展/产出、状态
- 不粘贴原始对话，不暴露敏感内容
- 过滤无关会话（测试、中止、无关闲聊）
- 更新 `key_topics`（3-8 个）
- 删除 `_raw_sessions` 后再发布

### Step 3：发布

**同事（默认）：**

```bash
python scripts/publish_daily.py --date today --db-only
```

**主管：**

```bash
python scripts/publish_daily.py --date today --git-push
```

或批量同步全员：`python scripts/export_db_to_git.py --date today --push`

### Step 4：回报

向用户说明：用户名、日期、会话数/轮次、是否已入库、是否已 push（主管）。

## 空日报

若 `total_sessions = 0`，仍发布，`daily_summary` 写：

> 今日未检测到 Cursor 会话记录。

## 权限说明

查询命令（主管用）：

```bash
python scripts/query_team.py --scope
python scripts/query_team.py --status
```

## 禁止事项

- 不要把 `.env` 密码写入对话或代码
- 不要把 `cursor_workspace` 指向本日报仓库
- 同事不要 git push

## 故障排查

| 现象 | 处理 |
|------|------|
| 找不到 transcripts | 检查 `cursor_workspace` 是否为日常业务项目 |
| 数据库失败 | 检查 `.env` 的 DB_PASSWORD |
| git push 失败 | 本地 commit 已保留，稍后重跑 `export_db_to_git.py --push` |

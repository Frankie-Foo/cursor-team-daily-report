---
name: cursor-daily-report
description: >-
  生成并发布 Cursor 团队日报：解析 agent-transcripts、写入 PostgreSQL、同步 Git。
  Use when user asks for daily cursor report, team activity summary, end-of-day
  cursor summary, or when scheduled automation runs the daily report workflow.
---

# Cursor 团队日报 Skill

## 适用场景

- 用户说：「发今日日报」「运行 cursor daily report」「总结今天 Cursor 做了什么」
- Cursor Automation 工作日 17:30 定时触发

## 前置检查

执行前确认仓库根目录存在：

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
- [ ] 3. 发布：写文件 + 入库 + git push
- [ ] 4. 回报结果路径
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

**模板示例：**

```markdown
今日 Cursor 工作摘要：
- 【数据岗位 PDCA 脚本优化】使用 Read/Shell 调整 publish 流程，已完成
- 【团队日报 Skill 部署】编写成员文档并 push 到 GitHub，已完成
```

### Step 3：发布

优先使用一键命令（自动读 user.json）：

```bash
python scripts/publish_daily.py --date today --git-push
```

若 Step 2 已手工改好 JSON，写入 `daily/<username>/YYYY-MM-DD.json` 后：

```bash
python scripts/db_writer.py --file daily/<username>/YYYY-MM-DD.json --type daily
python scripts/git_sync.py
```

### Step 4：回报

向用户说明：

- 用户名、日期
- 会话数 / 轮次
- 文件路径
- 是否已入库、已 push

## 空日报

若 `total_sessions = 0`，仍发布，`daily_summary` 写：

> 今日未检测到 Cursor 会话记录。

## 权限说明

查询命令（主管用）：

```bash
python scripts/query_team.py --scope
python scripts/query_team.py --status
```

成员无需运行查询；发布只需 `publish_daily.py`。

## 禁止事项

- 不要把 `.env` 密码写入对话或代码
- 不要把 `cursor_workspace` 指向本日报仓库
- 不要跳过 git push（除非用户明确要求）

## 故障排查

| 现象 | 处理 |
|------|------|
| 找不到 transcripts | 检查 `cursor_workspace` 是否为日常业务项目 |
| 数据库失败 | 检查 `.env` 的 DB_PASSWORD |
| git push 失败 | 本地 commit 已保留，稍后重跑 `python scripts/git_sync.py` |

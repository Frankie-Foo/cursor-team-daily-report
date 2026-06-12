---
name: cursor-daily-report
description: >-
  生成 Cursor 团队日报：解析 agent-transcripts、输出结构化 JSON/Markdown、
  写入 PostgreSQL，并可选 git push。Use when the user asks for daily cursor report,
  team activity summary, cursor daily summary, or when a scheduled automation runs
  the daily report workflow.
---

# Cursor 团队日报

## 前置条件

1. 已 clone 本仓库并安装依赖：`pip install -r requirements.txt`
2. 已配置 `.env`（参考 `.env.example`）
3. 已配置 `config/user.json` 中的 `username`
4. 已初始化数据库：`python scripts/db_schema.py --create-db`

## 标准流程

```
Task Progress:
- [ ] Step 1: 解析当天 transcripts（指定 --workspace 为实际 Cursor 项目路径）
- [ ] Step 2: AI 精炼 daily_summary（详细版）
- [ ] Step 3: 写入 daily/<username>/ JSON + Markdown
- [ ] Step 4: 写入 PostgreSQL
- [ ] Step 5: git commit + push
```

### Step 1: 解析

```bash
python scripts/parse_transcripts.py --date today --workspace "<Cursor项目路径>" --output .tmp/parsed.json
```

### Step 2: 精炼摘要

基于 `_raw_sessions` 用中文写 3-6 条 bullet，更新 `daily_summary` 和 `key_topics`，删除 `_raw_sessions`。

### Step 3-5: 发布

```bash
python scripts/publish_daily.py --date today --workspace "<Cursor项目路径>" --git-push
```

## 查询（带权限）

```bash
python scripts/query_team.py --scope
python scripts/query_team.py --status
python scripts/query_team.py --viewer May --ranking --month 2026-06
```

## 注意

- `--workspace` 填成员实际干活的 Cursor 项目，不是本日报仓库路径
- 权限由 `config/org.json` + 本地 `username` 决定，无需登录账号

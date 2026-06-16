# Cursor Automation — 统一日报（固定每日 POST）

## 同事 · Cursor Automation

| 字段 | 值 |
|------|-----|
| 名称 | Cursor 统一日报 |
| Cron | `30 17 * * 1-5` |
| 时区 | Asia/Shanghai |
| Skill | `cursor-daily-report` |

### Prompt（复制）

```text
读取 cursor-daily-report skill，执行今日统一日报并 POST（固定流程，不要 Git）：

cd 到 skill 目录，运行：
python scripts/build_unified_daily.py --date today --api-only

成功后回报：user、date、submitted、sections 概览（Vertu 任务数、Vemory 会议数、Cursor 会话数）。
失败则说明原因（vertu 未登录、API Token、odoo_user_id 等）。
```

---

## 同事 · Windows 计划任务（不依赖 Cursor 开着）

安装 Skill 后执行一次：

```powershell
powershell -ExecutionPolicy Bypass -File install_daily_task.ps1
```

效果：**工作日 17:30** 自动跑 `run_daily.ps1` → 三源聚合 → POST API。

---

## 主管 · 可选定时

| 任务 | Cron | 命令 |
|------|------|------|
| DB → Git | `0 18 * * 1-5` | `scripts/frank_sync_git.ps1` |
| API 服务 | 常驻 | `scripts/run_api.ps1` |

---

## 固定 POST 命令（唯一标准）

```powershell
python scripts/build_unified_daily.py --date today --api-only
```

等价：`powershell -File run_daily.ps1`

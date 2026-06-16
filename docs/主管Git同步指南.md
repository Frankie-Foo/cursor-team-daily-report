# 主管 Git 同步指南

> 同事只写 PostgreSQL；Git 备份由 Frank 统一维护。

---

## 架构

```
同事 Skill  --db-only-->  PostgreSQL  --export-->  Git (本仓库 daily/)
```

- 同事：**不需要** Git / GitHub
- 主管：定时从数据库导出到 `daily/<user>/`，commit + push

---

## 每日同步（推荐）

在 `cursor-team-daily-report` 仓库根目录：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/frank_sync_git.ps1
```

等价于：

```powershell
python scripts/export_db_to_git.py --date today --push
```

---

## 常用命令

```powershell
# 查看今天谁交了日报
python scripts/query_team.py --status

# 导出指定日期（不 push）
python scripts/export_db_to_git.py --date 2026-06-12

# 导出并 push
python scripts/export_db_to_git.py --date today --push

# 主管自己发日报（写库 + 本地文件 + push）
python scripts/publish_daily.py --date today --git-push
```

---

## 分发给同事

1. 运行 `scripts/build_colleague_package.ps1` 生成 zip
2. 把 `package/colleague/cursor-team-daily-report.zip` 发给同事
3. 附上 `package/colleague/同事使用说明.md`
4. **私发**数据库密码（`.env` 里的 `DB_PASSWORD`）

同事三件装：**Skill 文件夹 + 说明文档 + 数据库密码**。

---

## 可选：定时任务

Windows 任务计划程序，工作日 18:00 执行：

```
powershell -ExecutionPolicy Bypass -File D:\cursor-team-daily-report\scripts\frank_sync_git.ps1
```

---

*2026-06-12*

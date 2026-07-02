# Cursor 团队日报 — MCP（同事版）

在 Cursor 里一句话总结今天的工作并提交日报，不用手敲命令。

---

## 安装（就一步）

解压主管私发的个人包，**双击 `SETUP.bat`**，然后 **重启 Cursor**。

> 脚本会自动装依赖、写好 Token 和配置、注册 17:30 定时任务、装好这个 MCP。
> 你不用手动改任何文件。

---

## 验证装好了

在 Cursor 里说：

> 用 cursor-team-daily-report mcp 的 check_setup 检查一下

看到 `ok: true` 就成了。不是的话把 `problems` 发给主管。

---

## 每天怎么用

**手动**：直接对 Cursor说

> 总结我今天在 Cursor 里的工作并提交日报

**自动**：工作日 17:30 会自动提交（SETUP.bat 已帮你设好定时任务，不用管）。

---

## 出问题怎么办

| 现象 | 找谁 / 怎么办 |
|------|------|
| MCP 没连上 | 重启 Cursor；还不行就把 `problems` 发主管 |
| `check_setup` 不是 ok | 把返回的 `problems` 整段发给主管 |
| 提交 401 | 找主管/运维，Token 没同步 |
| 会话数为 0 | 跟主管说，`cursor_workspace` 路径可能不对 |

---

## 给主管/技术参考：工具清单

| 工具 | 作用 |
|------|------|
| `check_setup` | 检查 配置 / API 连通 / vertu 登录 |
| `test_api` | 健康检查团队 API |
| `preview_sessions` | 预览当天 Cursor 会话（不提交） |
| `generate_cursor_daily` | 生成 Cursor 日报 JSON（不提交） |
| `generate_unified_daily` | 生成 Vertu+Vemory+Cursor 统一日报（不提交） |
| `submit_daily_report` | POST 日报到 API（可覆盖摘要） |
| `submit_my_cursor_daily` | 一键：Cursor 日报生成 + 提交 |
| `submit_my_unified_daily` | 一键：统一日报生成 + 提交 |

提交日志：`logs/mcp_submissions.log`

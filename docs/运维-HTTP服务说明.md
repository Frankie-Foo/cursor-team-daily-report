# 运维说明：这就是 HTTP 服务接口

> 给运维同事：**不是 Cursor Skill，不是脚本包。仓库里有一个 FastAPI Web 服务，需要常驻跑在 8080，Nginx 反代到公网。**

---

## 1. 架构（一句话）

```
同事 Cursor Skill  --POST JSON-->  FastAPI (8080)  -->  PostgreSQL
```

- **服务端**：`api/server.py`（FastAPI + uvicorn）
- **客户端**：同事电脑上的 Skill + `submit_report.py`（只负责 POST，**不是**服务端）

---

## 2. HTTP 接口（已写好）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查，无需鉴权 |
| POST | `/api/v1/daily-reports` | 提交日报 JSON，Bearer Token 鉴权，写入 PostgreSQL |

部署成功后可在浏览器打开 **Swagger 文档**：

```
https://global-pdca.vertu.cn/docs
```

---

## 3. 服务器上要做什么

```bash
git clone https://github.com/Frankie-Foo/cursor-team-daily-report.git
cd cursor-team-daily-report
```

向 Frank 索取并放入（不在 Git 里）：

- `.env`（数据库连接）
- `config/api_tokens.json`

**方式 A — Docker（运维推荐）：**

```bash
docker compose up -d --build
```

详见 [Docker部署.md](Docker部署.md)。`.env` 里 `DB_HOST` 建议改为 `host.docker.internal`。

**方式 B — PowerShell 裸机：**

```powershell
powershell -File scripts/deploy_server.ps1 -PublicUrl https://global-pdca.vertu.cn
```

**开机自启（推荐，不用一直开 PowerShell 窗口）：**

以 **管理员** 打开 PowerShell：

```powershell
powershell -File scripts/install_api_server_task.ps1 -StartNow
```

- 计划任务名：`CursorTeamDailyReport-API-Server`
- 触发：系统启动 + 用户登录
- 日志：`logs\api-server.log`
- 查看状态：`powershell -File scripts/status_api_server_task.ps1`
- 卸载：`powershell -File scripts/uninstall_api_server_task.ps1`

> 请先在同一管理员窗口跑过 `deploy_server.ps1`（`pip install`），确保 SYSTEM 账户能用到 Python 依赖。

临时手动启动（调试用）：

```powershell
powershell -File scripts/run_api_server.ps1
```

**Nginx 反代：**

```
https://global-pdca.vertu.cn  →  http://127.0.0.1:8080
```

参考：`config/nginx-global-pdca.example.conf`

---

## 4. 验收

```powershell
curl https://global-pdca.vertu.cn/api/v1/health
```

期望返回：

```json
{"status":"ok","service":"cursor-team-daily-report"}
```

---

## 5. 常见误解

| 误解 | 实际 |
|------|------|
| 「只有 Skill / 脚本，没有接口」 | 接口在 `api/server.py`，必须 `run_api_server.ps1` 启动 |
| 「同事 zip 就是服务端」 | 同事 zip 是**客户端**，只 POST 到公网 API |
| 「clone 下来就能访问」 | 还要装依赖、拷 `.env`、**启动 uvicorn**、配 Nginx |

---

*Frank 侧本地已验证：`http://127.0.0.1:8080/api/v1/health` 返回 200。*

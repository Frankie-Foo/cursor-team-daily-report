# API 部署指南（主管）

同事 **只 POST**，数据库凭证仅在你这台服务端。

**外网同事无法访问 `10.100.x.x`。** 正式环境请 **[服务器部署.md](./服务器部署.md)**（运维反代 `global-pdca.vertu.cn`）。

---

## 架构

```
同事（公网） --HTTPS POST--> Cloudflare Tunnel / 反代 --> FastAPI (8080) --> PostgreSQL
你（内网）   query_team / export_db_to_git --> Git
```

---

## 1. 安装依赖

```powershell
cd D:\cursor-team-daily-report
pip install -r requirements.txt
winget install Cloudflare.cloudflared
```

---

## 2. 配置 .env

```env
DB_HOST=10.100.0.176
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=你的密码
DB_NAME=cursor_team_reports

# 公网地址（同事 .env 也填这个）
REPORT_API_URL=https://cursor-reports.你的域名.com
API_HOST=127.0.0.1
API_PORT=8080
CLOUDFLARE_TUNNEL_CONFIG=D:/cursor-team-daily-report/config/cloudflare-tunnel.yml
```

---

## 3. 生成每人 API Token

```powershell
python scripts/generate_api_tokens.py
```

---

## 4. 启动 API + 公网隧道

**临时验证（URL 会变）：**

```powershell
# 终端 1
powershell -File scripts/run_api.ps1
# 终端 2
powershell -File scripts/run_cloudflare_quick_tunnel.ps1
# 把打印的 https URL 写入 .env REPORT_API_URL
```

**正式固定域名：**

```powershell
powershell -File scripts/run_api_public.ps1
powershell -File scripts/install_api_public_task.ps1
```

外网验证：

```powershell
curl https://你的公网域名/api/v1/health
```

---

## 5. 分发给同事

| 发给同事 | 内容 |
|----------|------|
| zip | `package/colleague/cursor-team-daily-report.zip` |
| 说明 | `package/colleague/使用说明.md` |
| 私发 | 个人 `REPORT_API_TOKEN` |
| **公知** | **`REPORT_API_URL=你的公网 HTTPS 地址`** |

```powershell
powershell -File scripts/build_colleague_package.ps1
python scripts/export_member_credentials.py
```

---

## 6. 日常运维

```powershell
python scripts/query_team.py --viewer Frank --status
powershell -File scripts/frank_sync_git.ps1
```

---

*2026-06-15*

# Docker 部署（给运维）

> PostgreSQL **已有**（`10.100.0.176:5432`），本容器只跑 **FastAPI API**，不自带数据库。

---

## 1. 准备文件

```bash
git clone https://github.com/Frankie-Foo/cursor-team-daily-report.git
cd cursor-team-daily-report
```

向 Frank 索取并放入：

| 文件 | 说明 |
|------|------|
| `.env` | 数据库连接等 |
| `config/api_tokens.json` | 全员 API Token |

`.env` 里 **Docker 注意改 DB_HOST**：

```env
# 容器访问宿主机上的 PostgreSQL（Linux Docker）
DB_HOST=host.docker.internal
# 若 host.docker.internal 不通，改用宿主机内网 IP，例如：
# DB_HOST=10.100.0.176

API_HOST=0.0.0.0
API_PORT=8080
REPORT_API_URL=https://global-pdca.vertu.cn
```

---

## 2. 构建并启动

```bash
docker compose up -d --build
```

---

## 3. 验收

```bash
curl http://127.0.0.1:8080/api/v1/health
# {"status":"ok","service":"cursor-team-daily-report"}

docker compose logs -f api
```

Nginx 反代（与之前相同）：

```
https://global-pdca.vertu.cn  →  http://127.0.0.1:8080
```

Swagger：`https://global-pdca.vertu.cn/docs`

---

## 4. 常用命令

```bash
docker compose ps
docker compose restart api
docker compose down
docker compose up -d --build   # 更新代码后重建
```

---

## 5. 与 PowerShell 方案的关系

| 方式 | 适合 |
|------|------|
| **Docker**（本文） | 运维熟悉容器、要标准化部署 |
| `install_api_server_task.ps1` | Windows 裸机、不装 Docker |

两种方式都是同一个 FastAPI 服务，接口不变。

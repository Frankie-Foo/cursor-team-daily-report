# 运维：同步 API Token 到服务器

> 作用：让服务器认识新增同事的 API Token，否则他们提交日报会 **401**。
> 推荐方式：**Docker 热更新（docker cp）**，无需重启容器。

---

## 背景

本次新增 5 人：**Miranda、Bianca、Gao、Terry、Chen**。
他们的 Token 已生成在本地 `config/api_tokens.json`，但服务器容器里的还是旧的，需要覆盖更新。

| 项目 | 值 |
|------|-----|
| 服务器 API 地址 | `https://global-pdca.vertu.cn` |
| 容器名 | `cursor-team-daily-report-api` |
| 容器内目标路径 | `/app/config/api_tokens.json` |
| 是否需要重启 | **否**，覆盖后下一次 POST 即生效 |

---

## 操作步骤（推荐：docker cp 热更新）

### 1. 拿到更新包

主管私发的 `api_tokens-update.zip`，解压后得到：

```
config/api_tokens.json   ← 全员最新 Token
```

### 2. 把文件拷进容器

在**运行 API 的那台服务器**上执行：

```bash
docker cp config/api_tokens.json cursor-team-daily-report-api:/app/config/api_tokens.json
```

> 如果容器名不同，先 `docker ps` 找到运行 `cursor-team-daily-report` 镜像的容器名再替换。

### 3. 验证（用新 Token 测一次真实提交）

```bash
curl -X POST https://global-pdca.vertu.cn/api/v1/daily-reports \
  -H "Authorization: Bearer <新Token>" \
  -H "Content-Type: application/json" \
  -d '{"user":"Bianca","date":"2026-07-02","daily_summary":"ops验证","total_sessions":0,"total_turns":0,"key_topics":[],"all_files_modified":[],"sessions":[]}'
```

- 返回 **200**（或带 `id` 的 JSON）→ 生效 ✅
- 返回 **401** → Token 没覆盖成功，重做第 2 步
- 返回 **403** → Token 对应的用户名和提交的 `user` 不一致（正常保护机制，换个匹配的测）

> 健康检查 `curl https://global-pdca.vertu.cn/api/v1/health` 不要 token 也能通，**不能**用来验证 Token 是否生效，必须用上面的 POST 测。

---

## 本次新增的 5 个 Token（供运维核对）

| username | 中文名 | odoo_user_id |
|----------|--------|------|
| Miranda | 刘雪梅 | 14461 |
| Bianca | 廖静思 | 14468 |
| Gao | 高永强 | 14464 |
| Terry | 涂钢 | 14466 |
| Chen | 陈鹏飞 | 14474 |

> Token 明文不写在本表里，一律以 zip 中的 `api_tokens.json` 为准，勿群发。

---

## 如果 docker cp 不可行（备选）

### 备选 B：admin 接口热推（需服务器镜像已含 admin 路由）

主管本机执行（用 Frank 的 Token 调管理接口）：

```powershell
powershell -File scripts\push_server_tokens.ps1 -Users Miranda,Bianca,Gao,Terry,Chen
```

输出 `HTTP 200` 即成功。若报 404，说明服务器镜像较旧没有 admin 路由，回到方案 A。

### 备选 C：git pull + 重建（不推荐拿 Token）

```bash
git pull && docker compose up -d --build
```

⚠️ `api_tokens.json` 是敏感文件，**不在 git 里**，`git pull` 拿不到新 Token。用这条路必须再配合方案 A 的 `docker cp` 补一次 Token。

---

## 安全约定

- `api_tokens.json` 仅运维持有，**不入 git、不发群**
- 验证用的测试 Token 用完即弃，不要留在 shell 历史
- 容器内 `/app/config/api_tokens.json` 权限保持仅应用可读

---

## 故障排查

| 现象 | 处理 |
|------|------|
| `docker cp` 报容器不存在 | `docker ps -a` 确认容器名 |
| 同事仍 401 | 确认覆盖的是**运行中**那个容器；多个容器要每个都 cp |
| 同事 403 | 他们 `user.json` 里的 `username` 和 Token 绑定的用户名不一致，让主管核对 |
| 服务器 502/连不上 | 不是 Token 问题，看 API 容器和反代是否在跑 |

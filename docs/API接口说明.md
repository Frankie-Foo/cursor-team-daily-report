# API 接口说明

## 架构

```
同事终端 Skill  →  整理 JSON  →  POST  →  你的 API  →  PostgreSQL
```

---

## 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/daily-reports` | 提交日报（入库） |

基址：`http://10.100.0.176:8080`

---

## 鉴权

```
Authorization: Bearer <个人Token>
```

`user` 字段必须与 Token 对应用户一致。

---

## POST /api/v1/daily-reports

请求体结构见 **[数据结构.md](数据结构.md)**。

响应：

```json
{
  "ok": true,
  "user": "Ivan",
  "date": "2026-06-12",
  "total_sessions": 2,
  "total_turns": 8,
  "message": "已入库"
}
```

---

## 同事侧脚本对应

| 步骤 | 脚本 |
|------|------|
| 解析 | `parse_transcripts.py` |
| 整理 | Cursor Skill（改 draft.json） |
| POST | `submit_report.py` |
| 一键 | `run.ps1` |

---

*2026-06-12*

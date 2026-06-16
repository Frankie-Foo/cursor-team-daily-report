# Cursor 团队日报系统

## 架构

```
同事 --POST API--> FastAPI --> PostgreSQL --> Frank --Git-->
```

| 角色 | 做什么 |
|------|--------|
| **同事** | Skill → `POST /api/v1/daily-reports`（只有 API Token） |
| **主管** | 跑 API 服务、查库、同步 Git |

## 文档

| 文档 | 谁看 |
|------|------|
| [使用说明.md](package/colleague/使用说明.md) | 同事 |
| [API接口说明.md](docs/API接口说明.md) | 同事/对接 |
| [API部署指南.md](docs/API部署指南.md) | Frank |
| [Docker部署.md](docs/Docker部署.md) | 运维 |

## 主管命令

```powershell
python scripts/generate_api_tokens.py      # 生成 Token
powershell -File scripts/run_api.ps1         # 启动 API
powershell -File scripts/frank_sync_git.ps1  # DB -> Git
python scripts/query_team.py --status        # 提交状态
```

## 打包发给同事

```powershell
powershell -File scripts/build_colleague_package.ps1
```

输出：`package/colleague/cursor-team-daily-report.zip`

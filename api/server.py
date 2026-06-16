# -*- coding: utf-8 -*-
"""
Cursor 团队日报 API — 接收同事 POST，写入 PostgreSQL。

启动:
  powershell -File scripts/run_api.ps1
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
import psycopg2

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from api.auth import token_to_username
from api.schemas import DailyReportRequest, DailyReportResponse, prepare_report_payload
from db_writer import upsert_daily

app = FastAPI(
    title="Cursor Team Daily Report API",
    version="1.0.0",
    description="同事 Skill 整理日报后 POST 到此接口，服务端写入数据库。",
)


def require_username(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """
    从 Bearer 或 X-API-Key 解析用户名。

    @param authorization Authorization 头
    @param x_api_key X-API-Key 头
    @returns 已鉴权的 username
    """
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_api_key:
        token = x_api_key.strip()

    username = token_to_username(token)
    if not username:
        raise HTTPException(status_code=401, detail="无效或缺失 API Token")
    return username


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    """健康检查。"""
    return {"status": "ok", "service": "cursor-team-daily-report"}


@app.post("/api/v1/daily-reports", response_model=DailyReportResponse)
def submit_daily_report(
    payload: DailyReportRequest,
    username: str = Depends(require_username),
) -> DailyReportResponse:
    """
    接收同事 Skill 整理好的日报并入库。

    @param payload 日报 JSON（见 api/schemas.py）
    @param username Token 绑定用户
    """
    if payload.user != username:
        raise HTTPException(
            status_code=403,
            detail=f"Token 对应用户 {username}，不能提交 user={payload.user}",
        )

    report = prepare_report_payload(payload.model_dump())
    try:
        upsert_daily(report)
    except psycopg2.OperationalError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"数据库不可用: {exc}",
        ) from exc
    return DailyReportResponse(
        user=username,
        date=report["date"],
        total_sessions=report.get("total_sessions", 0),
        total_turns=report.get("total_turns", 0),
    )

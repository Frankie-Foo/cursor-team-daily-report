# -*- coding: utf-8 -*-
"""日报 API 数据结构（服务端与客户端共用）。"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class SessionRecord(BaseModel):
    """单条 Cursor 会话。"""

    id: str = ""
    summary: str = ""
    topics: list[str] = Field(default_factory=list)
    turns: int = 0
    tools_used: list[str] = Field(default_factory=list)
    files_touched: list[str] = Field(default_factory=list)
    outcome: str = "unknown"


class VertuTaskRecord(BaseModel):
    """Vertu 日报任务条目。"""

    title: str = ""
    progress: int = 0
    spent_hours: float = 0
    state: str = ""
    tomorrow_plan: str = ""


class VemoryMeetingRecord(BaseModel):
    """Vemory 会议条目。"""

    name: str = ""
    start_time: str = ""
    duration_minutes: int = 0
    summary: str = ""
    todos: list[str] = Field(default_factory=list)


class UnifiedSections(BaseModel):
    """统一日报三大板块。"""

    vertu: dict[str, Any] = Field(default_factory=dict)
    vemory: dict[str, Any] = Field(default_factory=dict)
    cursor: dict[str, Any] = Field(default_factory=dict)
    highlights: list[str] = Field(default_factory=list)


class DailyReportRequest(BaseModel):
    """
    POST /api/v1/daily-reports 请求体。

    report_kind=unified 时含 sections（Vertu + Vemory + Cursor）。
    """

    user: str
    date: str
    generated_at: str | None = None
    report_kind: str = "unified"
    total_sessions: int = 0
    total_turns: int = 0
    daily_summary: str = ""
    key_topics: list[str] = Field(default_factory=list)
    all_files_modified: list[str] = Field(default_factory=list)
    sessions: list[SessionRecord] = Field(default_factory=list)
    sections: UnifiedSections | None = None

    model_config = {"extra": "ignore"}

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        """校验日期格式 YYYY-MM-DD。"""
        parts = value.split("-")
        if len(parts) != 3:
            raise ValueError("date 必须为 YYYY-MM-DD")
        return value


class DailyReportResponse(BaseModel):
    """POST 成功响应。"""

    ok: bool = True
    user: str
    date: str
    total_sessions: int = 0
    total_turns: int = 0
    message: str = "已入库"


def prepare_report_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """
    清洗并校验日报 JSON，供 POST 使用。

    @param raw 解析或精炼后的日报 dict
    @returns 符合 API 契约的 dict
    """
    cleaned = dict(raw)
    cleaned.pop("_raw_sessions", None)
    model = DailyReportRequest.model_validate(cleaned)
    return model.model_dump(exclude_none=True)

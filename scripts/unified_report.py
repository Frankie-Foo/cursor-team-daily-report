# -*- coding: utf-8 -*-
"""统一日报 Markdown 渲染与摘要生成。"""

from __future__ import annotations

from typing import Any


def _first_line(text: str, limit: int = 120) -> str:
    """取首行并截断。"""
    line = (text or "").strip().splitlines()[0] if text else ""
    return line[:limit] + ("…" if len(line) > limit else "")


def parse_vertu_tasks(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    """
    从 Vertu user-summary 解析今日任务与 OKR。

    @param payload vertu daily-report user-summary 响应
    @returns (today_tasks, tomorrow_plans, okr_snapshot)
    """
    reports = payload.get("daily_reports") or []
    if not reports:
        return [], [], {}

    body = (reports[0].get("payload") or {})
    today_raw = body.get("today") or []
    tomorrow_raw = body.get("tomorrow") or []

    today: list[dict[str, Any]] = []
    for item in today_raw:
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        lines = title.split("\n")
        main_title = lines[0].strip()
        tomorrow_plan = ""
        for line in lines[1:]:
            if "明日" in line or "计划" in line:
                tomorrow_plan = line.strip()
                break
        today.append(
            {
                "title": main_title,
                "progress": int(item.get("progress") or 0),
                "spent_hours": float(item.get("spent_hours") or 0),
                "state": str(item.get("state_display") or item.get("state") or ""),
                "tomorrow_plan": tomorrow_plan,
            }
        )

    tomorrow: list[str] = []
    for item in tomorrow_raw:
        title = str(item.get("title") or "").strip()
        if title:
            tomorrow.append(title)

    okr_snapshot: dict[str, Any] = {}
    okrs = payload.get("okrs") or []
    if okrs:
        okr = okrs[0]
        krs = okr.get("key_results") or []
        if krs:
            kr = krs[0]
            okr_snapshot = {
                "title": str(okr.get("title") or ""),
                "target_amount": float(kr.get("target_amount") or 0),
                "actual_amount": float(kr.get("actual_amount") or 0),
                "completion_rate": float(kr.get("completion_rate") or 0),
            }

    return today, tomorrow, okr_snapshot


def parse_vemory_meetings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """
    从 Vemory meetings 响应解析会议列表。

    @param payload vemory meetings JSON
    @returns 规范化会议列表
    """
    meetings: list[dict[str, Any]] = []
    for item in payload.get("meetings") or []:
        todos = [
            str(t.get("content") or "").strip()
            for t in (item.get("todos") or [])
            if str(t.get("content") or "").strip()
        ]
        duration_sec = int(item.get("duration_seconds") or 0)
        meetings.append(
            {
                "name": str(item.get("name") or "未命名会议"),
                "start_time": str(item.get("start_time") or ""),
                "duration_minutes": max(1, duration_sec // 60) if duration_sec else 0,
                "summary": _first_line(str(item.get("summary") or ""), 300),
                "todos": todos[:5],
            }
        )
    return meetings


def build_highlights(
    vertu_tasks: list[dict[str, Any]],
    okr: dict[str, Any],
    vemory_meetings: list[dict[str, Any]],
    cursor_sessions: list[dict[str, Any]],
) -> list[str]:
    """
    生成重点事项 bullet。

    @param vertu_tasks Vertu 今日任务
    @param okr OKR 快照
    @param vemory_meetings 会议列表
    @param cursor_sessions Cursor 会话
    @returns 重点事项列表
    """
    highlights: list[str] = []

    if okr:
        rate = okr.get("completion_rate", 0)
        if rate and rate < 30:
            highlights.append(
                f"业绩偏慢：完成率 {rate:.1f}%，需关注收款和 PO"
            )

    for task in vertu_tasks:
        title = task.get("title", "")
        progress = int(task.get("progress") or 0)
        if progress >= 75:
            highlights.append(f"高进展任务：{title[:40]}（{progress}%）")
        if "会议" in title or "Teams" in title:
            highlights.append(f"会议节点：{title[:50]}")
        if "付款" in title or "PO" in title.upper():
            highlights.append(f"收付款节点：{title[:50]}")

    if vemory_meetings:
        highlights.append(f"当日 Vemory 会议 {len(vemory_meetings)} 场，建议对照日报任务是否已覆盖")

    if not cursor_sessions:
        highlights.append("当日无 Cursor 会话记录")
    elif len(cursor_sessions) >= 3:
        highlights.append(f"Cursor 活跃：{len(cursor_sessions)} 个会话")

    return highlights[:8]


def render_unified_markdown(
    display_name: str,
    report_date: str,
    vertu_tasks: list[dict[str, Any]],
    tomorrow_plans: list[str],
    okr: dict[str, Any],
    vemory_meetings: list[dict[str, Any]],
    cursor_summary: str,
    cursor_sessions: list[dict[str, Any]],
    highlights: list[str],
) -> str:
    """
    渲染统一日报 Markdown（主管可读）。

    @returns 完整 Markdown 文本，写入 daily_summary
    """
    lines = [
        f"# 统一日报 — {display_name} — {report_date}",
        "",
    ]

    if okr:
        target_wan = okr.get("target_amount", 0) / 10000
        actual_wan = okr.get("actual_amount", 0) / 10000
        rate = okr.get("completion_rate", 0)
        lines.extend(
            [
                "## OKR 进度",
                "",
                f"- 目标：**{target_wan:.2f} 万** | 已入账：**{actual_wan:.2f} 万** | 完成率：**{rate:.1f}%**",
                "",
            ]
        )

    lines.extend(["## 一、Vertu 今日工作", ""])
    if vertu_tasks:
        lines.append("| 任务 | 进度 | 工时 | 状态 |")
        lines.append("|------|------|------|------|")
        total_hours = 0.0
        for task in vertu_tasks:
            hours = float(task.get("spent_hours") or 0)
            total_hours += hours
            title = str(task.get("title") or "").replace("|", "/")
            lines.append(
                f"| {title} | {task.get('progress', 0)}% | {hours:g}h | {task.get('state', '')} |"
            )
        lines.extend(["", f"**当日合计工时：约 {total_hours:g} 小时**", ""])
    else:
        lines.extend(["（当日无 Vertu 日报提交）", ""])

    lines.extend(["## 二、Vemory 当日会议", ""])
    if vemory_meetings:
        for idx, meeting in enumerate(vemory_meetings, 1):
            lines.append(
                f"### {idx}. {meeting.get('name', '')} "
                f"（{meeting.get('start_time', '')} · {meeting.get('duration_minutes', 0)} 分钟）"
            )
            lines.append("")
            if meeting.get("summary"):
                lines.append(meeting["summary"])
                lines.append("")
            if meeting.get("todos"):
                lines.append("**待办：**")
                for todo in meeting["todos"]:
                    lines.append(f"- {todo}")
                lines.append("")
    else:
        lines.extend(["（当日无 Vemory 会议）", ""])

    lines.extend(["## 三、Cursor 当日工作", ""])
    if cursor_summary.strip():
        lines.append(cursor_summary.strip())
        lines.append("")
    elif cursor_sessions:
        for session in cursor_sessions[:6]:
            lines.append(
                f"- 【{session.get('summary', '未命名')}】"
                f" 工具: {', '.join(session.get('tools_used', [])[:5]) or '无'}"
                f" | 状态: {session.get('outcome', 'unknown')}"
            )
        lines.append("")
    else:
        lines.extend(["（当日未检测到 Cursor 会话）", ""])

    lines.extend(["## 明日计划", ""])
    if tomorrow_plans:
        for plan in tomorrow_plans[:8]:
            lines.append(f"- {plan}")
    else:
        for task in vertu_tasks:
            plan = str(task.get("tomorrow_plan") or "").strip()
            if plan:
                lines.append(f"- {plan}")
    if not tomorrow_plans and not any(t.get("tomorrow_plan") for t in vertu_tasks):
        lines.append("- （待补充）")
    lines.append("")

    lines.extend(["## 重点事项", ""])
    for item in highlights:
        lines.append(f"- {item}")
    if not highlights:
        lines.append("- （无）")

    return "\n".join(lines)

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from ai_agent.api.schemas.common import fail, ok
from ai_agent.modules.cache.history import clear_history
from ai_agent.modules.db.dao import (
    clear_session_messages,
    delete_session,
    get_messages_by_session,
    get_sessions_paginated,
    search_messages,
    update_session_title,
)
from ai_agent.modules.llm.factory import get_llm

router = APIRouter()


class UpdateTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@router.get("/sessions")
def list_sessions(
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    size: int = Query(default=50, ge=1, le=200, description="每页条数"),
):
    """获取会话列表（分页，默认返回第一页 50 条）"""
    sessions, total = get_sessions_paginated(page, size)
    return ok({
        "total": total,
        "page": page,
        "size": size,
        "list": [
            {
                "session_id": s.session_id,
                "title": s.title,
                "created_time": s.created_time,
            }
            for s in sessions
        ],
    })


@router.get("/sessions/search")
def search_session_messages(
    q: str = Query(..., min_length=1, max_length=200, description="搜索关键词"),
    session_id: Optional[str] = Query(default=None, description="限定某个会话内搜索"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    """全文检索消息内容，支持按会话过滤（分页）"""
    messages, total = search_messages(q, session_id, page, size)
    return ok({
        "total": total,
        "page": page,
        "size": size,
        "keyword": q,
        "list": messages,
    })


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
    """查询某会话的全部消息"""
    messages = get_messages_by_session(session_id)
    return ok([
        {
            "role": m.role,
            "content": m.content,
            "created_time": m.created_time,
        }
        for m in messages
    ])


@router.get("/sessions/{session_id}/export")
def export_session(session_id: str):
    """导出会话完整记录为 JSON（可用于备份、分析、微调）"""
    messages = get_messages_by_session(session_id)
    return ok({
        "session_id": session_id,
        "exported_at": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "created_time": m.created_time.isoformat(),
            }
            for m in messages
        ],
    })


@router.get("/sessions/{session_id}/export/csv")
def export_session_csv(session_id: str):
    """将会话消息导出为 CSV 文件（适合数据分析、微调）"""
    messages = get_messages_by_session(session_id)
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["session_id", "role", "content", "created_time"],
        quoting=csv.QUOTE_ALL,
    )
    writer.writeheader()
    for m in messages:
        writer.writerow({
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "created_time": m.created_time.isoformat(),
        })
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="session_{session_id}.csv"'
        },
    )


@router.post("/sessions/{session_id}/auto-title")
async def auto_generate_title(session_id: str):
    """使用 LLM 根据对话内容自动生成会话标题。

    取前 4 条消息作为上下文，调用 LLM 生成 10-30 字的标题。
    """
    msgs = get_messages_by_session(session_id)
    if not msgs:
        return fail(400, "Session has no messages")

    snippet = "\n".join(
        f"{m.role}: {m.content[:300]}"
        for m in msgs[:4]
    )
    llm = get_llm()
    prompt = (
        "根据以下对话内容，生成一个简洁的会话标题（10–30个字，中文或英文均可）。\n"
        "只返回标题本身，不要加引号、解释或任何额外内容。\n\n"
        f"{snippet}"
    )
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    title = response.content.strip()[:200]

    updated = update_session_title(session_id, title)
    if not updated:
        return fail(404, "Session not found")
    return ok({"session_id": session_id, "title": title})


@router.put("/sessions/{session_id}/title")
def set_session_title(session_id: str, body: UpdateTitleRequest):
    """手动更新会话标题"""
    updated = update_session_title(session_id, body.title)
    if not updated:
        return fail(404, "Session not found")
    return ok({"session_id": session_id, "title": body.title})


@router.post("/sessions/{session_id}/clear")
def clear_session(session_id: str):
    """清空会话消息（保留会话记录，开始新对话）"""
    count = clear_session_messages(session_id)
    clear_history(session_id)
    return ok({"session_id": session_id, "cleared": count})


@router.delete("/sessions/{session_id}")
def remove_session(session_id: str):
    """删除会话及其全部消息"""
    delete_session(session_id)
    return ok()

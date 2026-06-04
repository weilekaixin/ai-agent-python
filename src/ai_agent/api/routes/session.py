from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from ai_agent.api.schemas.common import fail, ok
from ai_agent.modules.cache.history import clear_history
from ai_agent.modules.db.dao import (
    clear_session_messages,
    delete_session,
    get_messages_by_session,
    get_sessions_paginated,
    update_session_title,
)

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


@router.put("/sessions/{session_id}/title")
def set_session_title(session_id: str, body: UpdateTitleRequest):
    """更新会话标题"""
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

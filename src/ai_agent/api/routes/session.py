from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ai_agent.api.schemas.common import fail, ok
from ai_agent.modules.db.dao import (
    delete_session,
    get_messages_by_session,
    get_sessions,
    update_session_title,
)

router = APIRouter()


class UpdateTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


@router.get("/sessions")
def list_sessions():
    """获取全部会话列表（按创建时间降序）"""
    sessions = get_sessions()
    return ok([
        {
            "session_id": s.session_id,
            "title": s.title,
            "created_time": s.created_time,
        }
        for s in sessions
    ])


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


@router.delete("/sessions/{session_id}")
def remove_session(session_id: str):
    """删除会话及其全部消息"""
    delete_session(session_id)
    return ok()

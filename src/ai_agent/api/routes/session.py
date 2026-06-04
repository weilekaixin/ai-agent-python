from fastapi import APIRouter

from ai_agent.api.schemas.common import ok
from ai_agent.modules.db.dao import get_messages_by_session, get_sessions, delete_session

router = APIRouter()


@router.get("/sessions")
def list_sessions():
    """获取全部会话列表"""
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


@router.delete("/sessions/{session_id}")
def remove_session(session_id: str):
    """删除会话及其全部消息"""
    delete_session(session_id)
    return ok()

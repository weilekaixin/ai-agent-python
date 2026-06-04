from fastapi import APIRouter

from ai_agent.api.schemas.common import fail, ok
from ai_agent.api.schemas.feedback import FeedbackCreate
from ai_agent.modules.db.dao import (
    create_or_update_feedback,
    get_feedback_by_message,
    get_feedback_by_session,
    get_feedback_stats,
    get_message_by_id,
)

router = APIRouter(tags=["feedback"])


@router.post("/messages/{message_id}/feedback")
async def submit_feedback(message_id: int, body: FeedbackCreate):
    """提交消息反馈（点赞/踩）。重复提交会更新已有反馈。"""
    msg = get_message_by_id(message_id)
    if msg is None:
        return fail(404, f"Message {message_id} not found")
    result = create_or_update_feedback(
        message_id=message_id,
        session_id=msg.session_id,
        rating=body.rating,
        comment=body.comment,
    )
    return ok(result)


@router.get("/messages/{message_id}/feedback")
async def get_message_feedback(message_id: int):
    """查询某条消息的反馈详情。"""
    result = get_feedback_by_message(message_id)
    if result is None:
        return fail(404, "No feedback found for this message")
    return ok(result)


@router.get("/sessions/{session_id}/feedback")
async def get_session_feedback(session_id: str):
    """查询某会话下所有消息的反馈列表。"""
    items = get_feedback_by_session(session_id)
    return ok({"session_id": session_id, "items": items, "total": len(items)})


@router.get("/sessions/{session_id}/feedback/stats")
async def get_session_feedback_stats(session_id: str):
    """统计某会话的反馈数据（总数、点赞数、踩数、好评率）。"""
    stats = get_feedback_stats(session_id)
    return ok(stats)

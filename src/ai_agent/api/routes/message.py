from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from ai_agent.api.schemas.common import fail, ok
from ai_agent.modules.db.dao import get_message_by_id, get_pinned_messages, pin_message, unpin_message

router = APIRouter(tags=["messages"])


class PinCreate(BaseModel):
    note: Optional[str] = None


@router.post("/messages/{message_id}/pin")
async def pin_a_message(message_id: int, body: PinCreate = None):
    """置顶/收藏一条消息，可附加备注。幂等：已置顶则更新备注。"""
    msg = get_message_by_id(message_id)
    if msg is None:
        return fail(404, f"Message {message_id} not found")
    note = body.note if body else None
    result = pin_message(message_id=message_id, session_id=msg.session_id, note=note)
    return ok(result)


@router.delete("/messages/{message_id}/pin")
async def unpin_a_message(message_id: int):
    """取消置顶/收藏。"""
    removed = unpin_message(message_id)
    if not removed:
        return fail(404, "Message is not pinned")
    return ok({"message_id": message_id, "unpinned": True})


@router.get("/sessions/{session_id}/pinned")
async def get_pinned(session_id: str):
    """列出某会话下所有已置顶的消息。"""
    items = get_pinned_messages(session_id)
    return ok({"session_id": session_id, "items": items, "total": len(items)})

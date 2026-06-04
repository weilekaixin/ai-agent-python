from fastapi import APIRouter, Query

from ai_agent.api.schemas.common import ok
from ai_agent.modules.db.dao import get_session_token_usage, get_token_usage_summary

router = APIRouter(tags=["usage"])


@router.get("/sessions/{session_id}/usage")
async def get_usage(
    session_id: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    """分页查询会话的 Token 用量明细。"""
    items, total = get_session_token_usage(session_id, page=page, size=size)
    return ok({"session_id": session_id, "items": items, "total": total, "page": page, "size": size})


@router.get("/sessions/{session_id}/usage/summary")
async def get_usage_summary(session_id: str):
    """汇总会话的 Token 用量（请求次数、输入/输出 Token 总计）。"""
    return ok(get_token_usage_summary(session_id))

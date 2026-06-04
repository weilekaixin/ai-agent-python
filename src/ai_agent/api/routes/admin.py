from fastapi import APIRouter

from ai_agent.api.schemas.common import ok
from ai_agent.modules.db.dao import get_global_stats

router = APIRouter(tags=["admin"])


@router.get("/admin/stats")
async def global_stats():
    """全局统计面板：会话、消息、Token 用量、反馈、标签、置顶等聂合指标。"""
    return ok(get_global_stats())

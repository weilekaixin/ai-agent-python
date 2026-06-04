from fastapi import APIRouter, Query
from pydantic import BaseModel

from ai_agent.api.schemas.common import fail, ok
from ai_agent.modules.db.dao import (
    add_session_tag,
    get_session_tags,
    get_sessions_by_tag,
    list_all_tags,
    remove_session_tag,
)

router = APIRouter(tags=["tags"])


class TagCreate(BaseModel):
    tag: str


@router.post("/sessions/{session_id}/tags")
async def add_tag(session_id: str, body: TagCreate):
    """为会话添加标签（幂等）。标签自动转小写。"""
    tag = body.tag.strip()
    if not tag:
        return fail(400, "tag 不能为空")
    result = add_session_tag(session_id, tag)
    return ok(result)


@router.delete("/sessions/{session_id}/tags/{tag}")
async def remove_tag(session_id: str, tag: str):
    """移除会话标签。"""
    removed = remove_session_tag(session_id, tag)
    if not removed:
        return fail(404, f"Tag '{tag}' not found on session")
    return ok({"session_id": session_id, "tag": tag, "removed": True})


@router.get("/sessions/{session_id}/tags")
async def get_tags(session_id: str):
    """查询会话的所有标签。"""
    tags = get_session_tags(session_id)
    return ok({"session_id": session_id, "tags": tags})


@router.get("/tags")
async def all_tags():
    """列出全局所有标签及使用次数。"""
    return ok(list_all_tags())


@router.get("/tags/{tag}/sessions")
async def sessions_by_tag(
    tag: str,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
):
    """按标签分页查询会话列表。"""
    session_ids, total = get_sessions_by_tag(tag, page=page, size=size)
    return ok({
        "tag": tag,
        "session_ids": session_ids,
        "total": total,
        "page": page,
        "size": size,
    })

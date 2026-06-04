from fastapi import APIRouter

from ai_agent.api.schemas.common import fail, ok
from ai_agent.api.schemas.persona import PersonaCreate, PersonaUpdate
from ai_agent.modules.db.dao import (
    create_persona,
    delete_persona,
    get_persona,
    list_personas,
    update_persona,
)

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("")
def get_personas():
    """查询所有活跃 Persona"""
    return ok(list_personas(active_only=True))


@router.post("")
def add_persona(body: PersonaCreate):
    """创建新 Persona，返回 persona_id"""
    result = create_persona(
        name=body.name,
        system_prompt=body.system_prompt,
        description=body.description,
        avatar=body.avatar,
    )
    return ok({"persona_id": result["persona_id"]})


@router.get("/{persona_id}")
def read_persona(persona_id: str):
    """获取单个 Persona 详情（含 system_prompt）"""
    p = get_persona(persona_id)
    if p is None:
        return fail(404, "Persona not found")
    return ok(p)


@router.put("/{persona_id}")
def modify_persona(persona_id: str, body: PersonaUpdate):
    """更新 Persona 字段，只更新非 None 的字段"""
    result = update_persona(
        persona_id,
        name=body.name,
        system_prompt=body.system_prompt,
        description=body.description,
        avatar=body.avatar,
        is_active=body.is_active,
    )
    if result is None:
        return fail(404, "Persona not found")
    return ok(result)


@router.delete("/{persona_id}")
def remove_persona(persona_id: str):
    """删除 Persona"""
    deleted = delete_persona(persona_id)
    if not deleted:
        return fail(404, "Persona not found")
    return ok({"deleted": persona_id})

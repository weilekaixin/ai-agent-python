import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import select

from ai_agent.modules.db.client import get_session
from ai_agent.modules.db.models import Conversation, Message, Persona


def save_message_to_db(session_id: str, role: str, content: str) -> None:
    """保存一条消息（commit 由 get_session 上下文管理器处理）"""
    with get_session() as session:
        conv = session.exec(
            select(Conversation).where(Conversation.session_id == session_id)
        ).first()
        if conv is None:
            conv = Conversation(session_id=session_id, title=content[:20])
            session.add(conv)
        msg = Message(session_id=session_id, role=role, content=content)
        session.add(msg)


def get_messages_by_session(session_id: str) -> list[Message]:
    """查询某会话的全部消息，按时间升序"""
    with get_session() as session:
        return list(session.exec(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.id)
        ).all())


def get_sessions() -> list[Conversation]:
    """查询全部会话，按创建时间降序"""
    with get_session() as session:
        return list(session.exec(
            select(Conversation).order_by(Conversation.created_time.desc())
        ).all())


def delete_session(session_id: str) -> None:
    """删除会话及其全部消息"""
    with get_session() as session:
        messages = list(session.exec(
            select(Message).where(Message.session_id == session_id)
        ).all())
        for msg in messages:
            session.delete(msg)
        conv = session.exec(
            select(Conversation).where(Conversation.session_id == session_id)
        ).first()
        if conv:
            session.delete(conv)


def update_session_title(session_id: str, title: str) -> bool:
    """更新会话标题，返回 False 表示会话不存在"""
    with get_session() as session:
        conv = session.exec(
            select(Conversation).where(Conversation.session_id == session_id)
        ).first()
        if conv is None:
            return False
        conv.title = title[:200]
        session.add(conv)
    return True


def clear_session_messages(session_id: str) -> int:
    """清空会话内所有消息，保留会话记录本身。返回删除的消息数量。"""
    with get_session() as session:
        messages = list(session.exec(
            select(Message).where(Message.session_id == session_id)
        ).all())
        count = len(messages)
        for msg in messages:
            session.delete(msg)
    return count


# ──────────── Persona CRUD ────────────

def _persona_to_dict(p: Persona) -> dict:
    return {
        "persona_id": p.persona_id,
        "name": p.name,
        "description": p.description,
        "system_prompt": p.system_prompt,
        "avatar": p.avatar,
        "is_active": p.is_active,
        "created_time": p.created_time.isoformat(),
        "updated_time": p.updated_time.isoformat(),
    }


def create_persona(
    name: str,
    system_prompt: str,
    description: Optional[str] = None,
    avatar: Optional[str] = None,
) -> dict:
    with get_session() as session:
        p = Persona(
            persona_id=uuid.uuid4().hex,
            name=name,
            description=description,
            system_prompt=system_prompt,
            avatar=avatar,
        )
        session.add(p)
        session.flush()  # populate auto-generated fields before session closes
        result = _persona_to_dict(p)
    return result


def get_persona(persona_id: str) -> Optional[dict]:
    with get_session() as session:
        p = session.exec(
            select(Persona).where(Persona.persona_id == persona_id)
        ).first()
        if p is None:
            return None
        return _persona_to_dict(p)


def list_personas(active_only: bool = True) -> list[dict]:
    with get_session() as session:
        q = select(Persona)
        if active_only:
            q = q.where(Persona.is_active == True)  # noqa: E712
        rows = session.exec(q.order_by(Persona.created_time.desc())).all()
        return [_persona_to_dict(p) for p in rows]


def update_persona(
    persona_id: str,
    name: Optional[str] = None,
    system_prompt: Optional[str] = None,
    description: Optional[str] = None,
    avatar: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[dict]:
    with get_session() as session:
        p = session.exec(
            select(Persona).where(Persona.persona_id == persona_id)
        ).first()
        if p is None:
            return None
        for attr, value in [
            ("name", name),
            ("system_prompt", system_prompt),
            ("description", description),
            ("avatar", avatar),
            ("is_active", is_active),
        ]:
            if value is not None:  # None = not provided; False is handled correctly
                setattr(p, attr, value)
        p.updated_time = datetime.now()
        session.add(p)
        result = _persona_to_dict(p)
    return result


def delete_persona(persona_id: str) -> bool:
    with get_session() as session:
        p = session.exec(
            select(Persona).where(Persona.persona_id == persona_id)
        ).first()
        if p is None:
            return False
        session.delete(p)
    return True

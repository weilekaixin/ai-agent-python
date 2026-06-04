import uuid
from collections import Counter
from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import func
from sqlmodel import select

from ai_agent.modules.db.client import get_session
from ai_agent.modules.db.models import (
    Conversation, Message, MessageFeedback, Persona,
    PinnedMessage, SessionTag, TokenUsage,
)


def save_message_to_db(session_id: str, role: str, content: str) -> None:
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
    with get_session() as session:
        return list(session.exec(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.id)
        ).all())


def get_message_by_id(message_id: int) -> Optional[Message]:
    with get_session() as session:
        return session.exec(
            select(Message).where(Message.id == message_id)
        ).first()


def get_sessions() -> list[Conversation]:
    with get_session() as session:
        return list(session.exec(
            select(Conversation).order_by(Conversation.created_time.desc())
        ).all())


def get_sessions_paginated(page: int = 1, size: int = 50) -> tuple[list[Conversation], int]:
    offset = max(0, (page - 1) * size)
    with get_session() as session:
        total = session.exec(
            select(func.count()).select_from(Conversation)
        ).one()
        rows = list(session.exec(
            select(Conversation)
            .order_by(Conversation.created_time.desc())
            .offset(offset)
            .limit(size)
        ).all())
    return rows, int(total)


def search_messages(
    keyword: str,
    session_id: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    if not keyword or not keyword.strip():
        return [], 0
    offset = max(0, (page - 1) * size)
    pattern = f"%{keyword}%"
    with get_session() as session:
        base_filter = Message.content.like(pattern)
        count_q = select(func.count()).select_from(Message).where(base_filter)
        data_q = select(Message).where(base_filter)
        if session_id:
            count_q = count_q.where(Message.session_id == session_id)
            data_q = data_q.where(Message.session_id == session_id)
        total = int(session.exec(count_q).one())
        rows = list(session.exec(
            data_q.order_by(Message.created_time.desc())
            .offset(offset)
            .limit(size)
        ).all())
    return [
        {
            "id": m.id,
            "session_id": m.session_id,
            "role": m.role,
            "content": m.content,
            "created_time": m.created_time.isoformat(),
        }
        for m in rows
    ], total


def delete_session(session_id: str) -> None:
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
        session.flush()
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
            if value is not None:
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


# ──────────── Message Feedback CRUD ────────────

def _feedback_to_dict(f: MessageFeedback) -> dict:
    return {
        "id": f.id,
        "feedback_id": f.feedback_id,
        "message_id": f.message_id,
        "session_id": f.session_id,
        "rating": f.rating,
        "comment": f.comment,
        "created_time": f.created_time.isoformat(),
    }


def create_or_update_feedback(
    message_id: int,
    session_id: str,
    rating: int,
    comment: Optional[str] = None,
) -> dict:
    with get_session() as session:
        existing = session.exec(
            select(MessageFeedback).where(MessageFeedback.message_id == message_id)
        ).first()
        if existing:
            existing.rating = rating
            existing.comment = comment
            existing.created_time = datetime.now()
            session.add(existing)
            session.flush()
            result = _feedback_to_dict(existing)
        else:
            fb = MessageFeedback(
                feedback_id=uuid.uuid4().hex,
                message_id=message_id,
                session_id=session_id,
                rating=rating,
                comment=comment,
            )
            session.add(fb)
            session.flush()
            result = _feedback_to_dict(fb)
    return result


def get_feedback_by_message(message_id: int) -> Optional[dict]:
    with get_session() as session:
        f = session.exec(
            select(MessageFeedback).where(MessageFeedback.message_id == message_id)
        ).first()
        return _feedback_to_dict(f) if f else None


def get_feedback_by_session(session_id: str) -> list[dict]:
    with get_session() as session:
        rows = list(session.exec(
            select(MessageFeedback)
            .where(MessageFeedback.session_id == session_id)
            .order_by(MessageFeedback.created_time.desc())
        ).all())
        return [_feedback_to_dict(f) for f in rows]


def get_feedback_stats(session_id: str) -> dict:
    with get_session() as session:
        rows = list(session.exec(
            select(MessageFeedback).where(MessageFeedback.session_id == session_id)
        ).all())
    total = len(rows)
    positive = sum(1 for f in rows if f.rating == 1)
    negative = total - positive
    return {
        "session_id": session_id,
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_rate": round(positive / total, 4) if total > 0 else 0.0,
    }


# ──────────── Session Tags ────────────

def _tag_to_dict(t: SessionTag) -> dict:
    return {
        "id": t.id,
        "session_id": t.session_id,
        "tag": t.tag,
        "created_time": t.created_time.isoformat(),
    }


def add_session_tag(session_id: str, tag: str) -> dict:
    tag = tag.strip().lower()[:100]
    with get_session() as db:
        existing = db.exec(
            select(SessionTag)
            .where(SessionTag.session_id == session_id)
            .where(SessionTag.tag == tag)
        ).first()
        if existing:
            return _tag_to_dict(existing)
        t = SessionTag(session_id=session_id, tag=tag)
        db.add(t)
        db.flush()
        return _tag_to_dict(t)


def remove_session_tag(session_id: str, tag: str) -> bool:
    tag = tag.strip().lower()
    with get_session() as db:
        t = db.exec(
            select(SessionTag)
            .where(SessionTag.session_id == session_id)
            .where(SessionTag.tag == tag)
        ).first()
        if t is None:
            return False
        db.delete(t)
    return True


def get_session_tags(session_id: str) -> list[str]:
    with get_session() as db:
        rows = db.exec(
            select(SessionTag)
            .where(SessionTag.session_id == session_id)
            .order_by(SessionTag.tag)
        ).all()
        return [r.tag for r in rows]


def get_sessions_by_tag(tag: str, page: int = 1, size: int = 20) -> tuple[list[str], int]:
    tag = tag.strip().lower()
    offset = max(0, (page - 1) * size)
    with get_session() as db:
        total = int(db.exec(
            select(func.count()).select_from(SessionTag).where(SessionTag.tag == tag)
        ).one())
        rows = db.exec(
            select(SessionTag)
            .where(SessionTag.tag == tag)
            .offset(offset)
            .limit(size)
        ).all()
        return [r.session_id for r in rows], total


def list_all_tags() -> list[dict]:
    with get_session() as db:
        rows = db.exec(select(SessionTag)).all()
    counts = Counter(r.tag for r in rows)
    return [{"tag": tag, "count": count} for tag, count in counts.most_common()]


# ──────────── Message Pinning ────────────

def _pin_to_dict(p: PinnedMessage) -> dict:
    return {
        "id": p.id,
        "message_id": p.message_id,
        "session_id": p.session_id,
        "note": p.note,
        "created_time": p.created_time.isoformat(),
    }


def pin_message(message_id: int, session_id: str, note: Optional[str] = None) -> dict:
    with get_session() as db:
        existing = db.exec(
            select(PinnedMessage).where(PinnedMessage.message_id == message_id)
        ).first()
        if existing:
            if note is not None:
                existing.note = note
                db.add(existing)
                db.flush()
            return _pin_to_dict(existing)
        pm = PinnedMessage(message_id=message_id, session_id=session_id, note=note)
        db.add(pm)
        db.flush()
        return _pin_to_dict(pm)


def unpin_message(message_id: int) -> bool:
    with get_session() as db:
        pm = db.exec(
            select(PinnedMessage).where(PinnedMessage.message_id == message_id)
        ).first()
        if pm is None:
            return False
        db.delete(pm)
    return True


def get_pinned_messages(session_id: str) -> list[dict]:
    with get_session() as db:
        rows = db.exec(
            select(PinnedMessage)
            .where(PinnedMessage.session_id == session_id)
            .order_by(PinnedMessage.created_time.desc())
        ).all()
        return [_pin_to_dict(p) for p in rows]


# ──────────── Token Usage ────────────

def _usage_to_dict(u: TokenUsage) -> dict:
    return {
        "id": u.id,
        "session_id": u.session_id,
        "input_tokens": u.input_tokens,
        "output_tokens": u.output_tokens,
        "total_tokens": u.total_tokens,
        "model": u.model,
        "created_time": u.created_time.isoformat(),
    }


def record_token_usage(
    session_id: str,
    input_tokens: int,
    output_tokens: int,
    model: str = "unknown",
) -> None:
    with get_session() as db:
        usage = TokenUsage(
            session_id=session_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            model=model,
        )
        db.add(usage)


def get_session_token_usage(
    session_id: str,
    page: int = 1,
    size: int = 20,
) -> tuple[list[dict], int]:
    offset = max(0, (page - 1) * size)
    with get_session() as db:
        total = int(db.exec(
            select(func.count()).select_from(TokenUsage)
            .where(TokenUsage.session_id == session_id)
        ).one())
        rows = db.exec(
            select(TokenUsage)
            .where(TokenUsage.session_id == session_id)
            .order_by(TokenUsage.created_time.desc())
            .offset(offset)
            .limit(size)
        ).all()
    return [_usage_to_dict(u) for u in rows], total


def get_token_usage_summary(session_id: str) -> dict:
    with get_session() as db:
        rows = db.exec(
            select(TokenUsage).where(TokenUsage.session_id == session_id)
        ).all()
    total_in = sum(r.input_tokens for r in rows)
    total_out = sum(r.output_tokens for r in rows)
    return {
        "session_id": session_id,
        "requests": len(rows),
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_tokens": total_in + total_out,
    }


# ──────────── Admin / Global Stats ────────────

def get_global_stats() -> dict:
    """全局统计面板：会话、消息、Token、反馈、标签、置顶等聂合指标。"""
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    with get_session() as db:
        total_sessions = int(db.exec(select(func.count()).select_from(Conversation)).one())
        today_sessions = int(db.exec(
            select(func.count()).select_from(Conversation)
            .where(Conversation.created_time >= today_start)
        ).one())

        total_messages = int(db.exec(select(func.count()).select_from(Message)).one())
        today_messages = int(db.exec(
            select(func.count()).select_from(Message)
            .where(Message.created_time >= today_start)
        ).one())
        human_count = int(db.exec(
            select(func.count()).select_from(Message).where(Message.role == "human")
        ).one())

        all_usage = list(db.exec(select(TokenUsage)).all())
        all_fb = list(db.exec(select(MessageFeedback)).all())
        all_tags = list(db.exec(select(SessionTag)).all())
        total_pinned = int(db.exec(select(func.count()).select_from(PinnedMessage)).one())
        total_personas = int(db.exec(select(func.count()).select_from(Persona)).one())

    total_in = sum(u.input_tokens for u in all_usage)
    total_out = sum(u.output_tokens for u in all_usage)
    fb_total = len(all_fb)
    fb_positive = sum(1 for f in all_fb if f.rating == 1)

    return {
        "sessions": {"total": total_sessions, "today": today_sessions},
        "messages": {
            "total": total_messages,
            "today": today_messages,
            "human": human_count,
            "ai": total_messages - human_count,
        },
        "tokens": {
            "requests": len(all_usage),
            "total_input": total_in,
            "total_output": total_out,
            "total": total_in + total_out,
        },
        "feedback": {
            "total": fb_total,
            "positive": fb_positive,
            "negative": fb_total - fb_positive,
            "positive_rate": round(fb_positive / fb_total, 4) if fb_total > 0 else 0.0,
        },
        "tags": {
            "total_assignments": len(all_tags),
            "distinct_tags": len({t.tag for t in all_tags}),
            "labeled_sessions": len({t.session_id for t in all_tags}),
        },
        "pinned_messages": {"total": total_pinned},
        "personas": {"total": total_personas},
    }

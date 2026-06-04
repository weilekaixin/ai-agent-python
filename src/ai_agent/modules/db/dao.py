from sqlmodel import select

from ai_agent.modules.db.client import get_session
from ai_agent.modules.db.models import Conversation, Message


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

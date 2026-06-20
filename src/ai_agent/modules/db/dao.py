from sqlmodel import select

from ai_agent.modules.db.client import get_session
from ai_agent.modules.db.models import Conversation, Message


def save_message_to_db(session_id: str, role: str, content: str) -> None:
    """保存一条消息到数据库"""
    with get_session() as session:
        # 会话不存在就创建
        conv = session.exec(
            select(Conversation).where(Conversation.session_id == session_id)
        ).first()
        if conv is None:
            conv = Conversation(session_id=session_id, title=content[:20])
            session.add(conv)

        # 存消息
        msg = Message(session_id=session_id, role=role, content=content)
        session.add(msg)
        session.commit()

from datetime import datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field


class Conversation(SQLModel, table=True):
    """会话表"""
    __tablename__ = "conversation"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(unique=True, index=True, max_length=36)
    title: Optional[str] = Field(default=None, max_length=200)
    created_time: datetime = Field(default_factory=datetime.now)


class Message(SQLModel, table=True):
    """消息表"""
    __tablename__ = "message"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, max_length=36)
    role: str = Field(max_length=20)  # human / ai
    content: str
    created_time: datetime = Field(default_factory=datetime.now)


class Persona(SQLModel, table=True):
    """自定义 AI 角色表（Custom GPTs / Gems 风格）"""
    __tablename__ = "persona"

    id: Optional[int] = Field(default=None, primary_key=True)
    persona_id: str = Field(unique=True, index=True, max_length=36)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    system_prompt: str
    avatar: Optional[str] = Field(default=None, max_length=200)
    is_active: bool = Field(default=True)
    created_time: datetime = Field(default_factory=datetime.now)
    updated_time: datetime = Field(default_factory=datetime.now)


class MessageFeedback(SQLModel, table=True):
    """消息反馈表（点赞 / 踩 + 可选评论，每条消息保留最新一条）"""
    __tablename__ = "message_feedback"

    id: Optional[int] = Field(default=None, primary_key=True)
    feedback_id: str = Field(unique=True, index=True, max_length=36)
    message_id: int = Field(index=True)
    session_id: str = Field(index=True, max_length=36)
    rating: int                                  # +1 thumbs-up, -1 thumbs-down
    comment: Optional[str] = Field(default=None, max_length=1000)
    created_time: datetime = Field(default_factory=datetime.now)


class SessionTag(SQLModel, table=True):
    """会话标签表（同一会话内标签不重复）"""
    __tablename__ = "session_tag"
    __table_args__ = (UniqueConstraint("session_id", "tag", name="uq_session_tag"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, max_length=36)
    tag: str = Field(max_length=100)
    created_time: datetime = Field(default_factory=datetime.now)


class PinnedMessage(SQLModel, table=True):
    """消息置顶/收藏表（每条消息最多置顶一次）"""
    __tablename__ = "pinned_message"

    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: int = Field(unique=True, index=True)
    session_id: str = Field(index=True, max_length=36)
    note: Optional[str] = Field(default=None, max_length=500)
    created_time: datetime = Field(default_factory=datetime.now)


class TokenUsage(SQLModel, table=True):
    """每次 AI 响应的 Token 用量记录"""
    __tablename__ = "token_usage"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True, max_length=36)
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)          # input + output
    model: str = Field(default="unknown", max_length=100)
    created_time: datetime = Field(default_factory=datetime.now)

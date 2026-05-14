from datetime import datetime
from typing import Optional

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

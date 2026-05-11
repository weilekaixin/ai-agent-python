# modules/memory/store.py
from ai_agent.models.constants import TEN_NUM
from ai_agent.models.domain.message import Message


class MemoryStore:
    """消息存储 内存实现"""

    def __init__(self):
        self.messages: list[Message] = []

    def append(self, role: str, content: str) -> None:
        """新增记忆"""
        self.messages.append(Message(role=role, content=content))

    def recent(self, n: int = TEN_NUM) -> list[Message]:
        """获取记忆"""
        return self.messages[-n:]

# modules/memory/store.py
from ai_agent.models.constants import *
from ai_agent.models.domain.message import Message, ToolCallMessage


class MemoryStore:
    """消息存储 内存实现"""

    def __init__(self):
        self.messages: list[Message | ToolCallMessage] = []

    def append(self, role: str, content: str, tool_call_id: str | None = None) -> None:
        """新增记忆"""
        if tool_call_id:
            message = Message(role=role, content=content, tool_call_id=tool_call_id)
        else:
            message = Message(role=role, content=content)
        self.messages.append(message)

    def append_tool_calls(self, tool_calls: list[dict]) -> None:
        """记录大模型需要使用的工具 帮助大模型理解是否调用完成"""
        self.messages.append(ToolCallMessage(role=ASSISTANT_ROLE, content=EMPTY_STR, tool_calls=tool_calls))

    def recent(self, n: int = TEN_NUM) -> list[Message | ToolCallMessage]:
        """获取记忆"""
        return self.messages[-n:]

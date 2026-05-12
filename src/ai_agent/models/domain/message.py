# models/domain/message.py
from typing import TypedDict, NotRequired


class Message(TypedDict):
    role: str
    content: str
    tool_call_id: NotRequired[str | None]

class ToolCallMessage(TypedDict):
    role: str
    content: str
    tool_calls: list[dict]
# models/domain/message.py
from typing import TypedDict


class Message(TypedDict):
    role: str
    content: str

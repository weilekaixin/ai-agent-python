from pydantic import BaseModel


class ChatRequest(BaseModel):
    """对话"""
    session_id: str
    message: str


class ResumeRequest(BaseModel):
    """确认敏感操作"""
    session_id: str
    approved: bool  # True 同意，False 拒绝

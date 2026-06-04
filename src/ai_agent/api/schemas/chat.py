from pydantic import BaseModel


class ChatRequest(BaseModel):
    """对话请求"""
    session_id: str
    message: str


class ResumeRequest(BaseModel):
    """确认/拒绝敏感操作"""
    session_id: str
    thread_id: str   # /chat 返回的 __INTERRUPT__ 信号中携带，用于定位 checkpoint
    approved: bool   # True 同意，False 拒绝

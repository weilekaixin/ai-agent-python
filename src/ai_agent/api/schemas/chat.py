from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """对话请求"""
    session_id: str = Field(..., min_length=1, max_length=36)
    message: str = Field(..., min_length=1, max_length=4000, description="用户消息，不超过4000字")
    persona_id: Optional[str] = Field(None, max_length=36, description="自定义 AI 角色 ID，注入 system_prompt")


class ResumeRequest(BaseModel):
    """确认/拒绝敏感操作"""
    session_id: str = Field(..., min_length=1, max_length=36)
    thread_id: str = Field(..., min_length=1, max_length=36, description="/chat 返回的 __INTERRUPT__ 中携带")
    approved: bool

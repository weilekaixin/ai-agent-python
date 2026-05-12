from langchain_openai import ChatOpenAI

from ai_agent.config.settings import settings
from ai_agent.models.constants import DEEPSEEK_MODEL, DEEPSEEK_BASE_URL
from ai_agent.models.domain.message import Message, ToolCallMessage
from ai_agent.modules.llm.base import LLMClient


class DeepSeekClient(LLMClient):
    """deepseek"""

    def __init__(self, model: str = DEEPSEEK_MODEL):
        """创建deepseek模型"""
        self.client = ChatOpenAI(
            api_key=settings.deepseek_api_key,
            model=model,
            base_url=DEEPSEEK_BASE_URL
        )

    async def chat(self, messages: list[Message | ToolCallMessage], tools: list[dict] | None = None) -> tuple[str, list[dict]]:
        response = await self.client.ainvoke(messages, tools=tools)
        if response.tool_calls:
            return "", [{"name": tc["name"], "args": tc["args"], "id": tc["id"]} for tc in response.tool_calls]
        return str(response.content or ""), []

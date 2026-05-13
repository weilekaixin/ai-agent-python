from typing import AsyncGenerator, Any

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
        self.tool_calls: list = []

    async def chat(self, messages: list[Message | ToolCallMessage], tools: list[dict] | None = None) -> tuple[
        str, list[dict]]:
        """一次性回复"""
        if tools:
            response = await self.client.ainvoke(messages, tools=tools)
        else:
            response = await self.client.ainvoke(messages)
        if response.tool_calls:
            return "", [{"name": tc["name"], "args": tc["args"], "id": tc["id"]} for tc in response.tool_calls]
        return str(response.content or ""), []

    async def astream_chat(self, messages, tools=None) -> AsyncGenerator[str | list[str | Any], None]:
        """流式回复"""
        self.tool_calls = []

        if tools:
            stream = self.client.astream(messages, tools=tools)
        else:
            stream = self.client.astream(messages)

        has_tool = False
        async for chunk in stream:
            if chunk.tool_call_chunks:
                has_tool = True
            if chunk.content:
                yield chunk.content

        if has_tool:
            result = await self.client.ainvoke(messages, tools=tools)
            if result.tool_calls:
                self.tool_calls = [
                    {"name": tc["name"], "args": tc["args"], "id": tc["id"]}
                    for tc in result.tool_calls
                ]

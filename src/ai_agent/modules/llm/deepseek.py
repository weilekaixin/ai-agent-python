from langchain_openai import ChatOpenAI

from ai_agent.models.constants import DEEPSEEK_MODEL, DEEPSEEK_BASE_URL, EMPTY_STR
from ai_agent.modules.llm.base import LLMClient
from ai_agent.config.settings import settings


class DeepSeekClient(LLMClient):
    """创建deepseek模型"""

    def __init__(self, model: str = DEEPSEEK_MODEL):
        self.client = ChatOpenAI(
            api_key=settings.deepseek_api_key,
            model=model,
            base_url=DEEPSEEK_BASE_URL
        )

    """
    调用 DeepSeek 对话接口
    """

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> tuple[str, list[dict]]:
        chunks = []
        async for chunk in self.client.astream(messages):
            chunks.append(chunk.content)
        return EMPTY_STR.join(chunks), []

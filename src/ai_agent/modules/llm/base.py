from abc import ABC, abstractmethod

from ai_agent.models.domain.message import Message


class LLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[Message], tools: list[dict] | None = None) -> tuple[str, list[dict]]:
        ...

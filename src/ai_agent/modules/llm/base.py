from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> tuple[str, list[dict]]:
        ...

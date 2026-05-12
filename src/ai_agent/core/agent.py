from ai_agent.models.constants import USER_ROLE, ASSISTANT_ROLE
from ai_agent.modules.llm.deepseek import DeepSeekClient
from ai_agent.modules.memory.store import MemoryStore
from ai_agent.modules.tool.registry import ToolRegistry


class Agent:
    def __init__(self, registry: ToolRegistry | None = None):
        self.llm = DeepSeekClient()
        self.memory = MemoryStore()
        self.registry = registry

    async def chat(self, message: str) -> str:
        # 存储当前问题的记忆到上下文
        self.memory.append(USER_ROLE, message)
        # 获取上下文
        messages = self.memory.recent()
        # registry != null ? registry.get_openai_tools() : null
        tools = self.registry.get_openai_tools() if self.registry else None
        # 相当于一个数据有两个值 我只想获取第一个 不关心第二个 调度大模型
        reply, _ = await self.llm.chat(messages, tools)
        # 将大模型的回复存入上下文
        self.memory.append(ASSISTANT_ROLE, reply)
        return reply

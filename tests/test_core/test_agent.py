import asyncio

from ai_agent.core.agent import Agent
from ai_agent.modules.tool.registry import ToolRegistry
from ai_agent.modules.tool.tools import GetTimeTool


async def test_agent_chat():
    agent = Agent()
    reply = await agent.chat("你好")
    print(f"AI: {reply}")


async def test_agent_with_tools():
    registry = ToolRegistry()
    registry.register(GetTimeTool())
    agent = Agent(registry=registry)
    reply = await agent.chat("现在几点？")
    print(f"AI: {reply}")


if __name__ == "__main__":
    asyncio.run(test_agent_with_tools())
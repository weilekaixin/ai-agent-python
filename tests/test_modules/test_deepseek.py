import asyncio

from ai_agent.models.constants import USER_ROLE
from ai_agent.models.domain.message import Message
from ai_agent.modules.llm.deepseek import DeepSeekClient


# 对话测试
async def test_chat():
    content = input("问题: ")
    client = DeepSeekClient()
    text, tools = await client.chat([Message(role=USER_ROLE, content=content)])
    print(text)


if __name__ == "__main__":
    asyncio.run(test_chat())

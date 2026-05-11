import asyncio
from ai_agent.modules.llm.deepseek import DeepSeekClient

# 对话测试
async def test_chat():
    content = input("问题: ")
    client = DeepSeekClient()
    text, tools = await client.chat([{"role": "user", "content": content}])
    print(text)


if __name__ == "__main__":
    asyncio.run(test_chat())

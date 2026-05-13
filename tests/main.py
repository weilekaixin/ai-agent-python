import asyncio

from ai_agent.modules.llm.factory import get_llm


async def agent():
    llm = get_llm()
    print(llm)
    result = await llm.ainvoke([{"role": "user", "content": "你好？"}])
    print(result.content)


if __name__ == '__main__':
    asyncio.run(agent())

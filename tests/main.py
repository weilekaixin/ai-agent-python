import asyncio

from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.tool.tools import get_current_time, calculator


async def agent():
    # 获取大模型
    llm = get_llm()
    # 注册工具
    llm_with_tools = llm.bind_tools([get_current_time, calculator])
    print(llm, llm_with_tools)
    result = await llm_with_tools.ainvoke([{"role": "user", "content": "现在几点了？"}])
    print(result)


if __name__ == '__main__':
    asyncio.run(agent())

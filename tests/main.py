import asyncio

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage

from ai_agent.models.constants import MESSAGES
from ai_agent.modules.llm.factory import get_llm
from ai_agent.modules.tool.tools import tools


async def test():
    # 获取大模型
    llm = get_llm()
    # 创建react大模型实现tools_call
    agent = create_agent(llm, tools)
    # 组装单次上下文
    result = await agent.ainvoke({MESSAGES: [HumanMessage(content="把当前时间的小时乘以十等于多少？")]})
    # 输出大模型回复
    print(result[MESSAGES][-1].content)


if __name__ == '__main__':
    asyncio.run(test())

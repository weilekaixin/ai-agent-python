from collections.abc import AsyncGenerator

from langchain_core.messages import HumanMessage


async def token_stream(agent, message: str) -> AsyncGenerator[str, None]:
    """从 agent.astream_events 中提取文本 token 流"""
    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=message)]},
        version="v2",
    ):
        if event["event"] == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield content

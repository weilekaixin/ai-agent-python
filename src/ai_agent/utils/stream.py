from typing import AsyncGenerator

from langchain_core.messages import BaseMessage


async def token_stream(agent, messages: list[BaseMessage], session_id: str) -> AsyncGenerator[str, None]:
    try:
        config = {"configurable": {"thread_id": session_id}}
        async for event in agent.astream_events(
                {"messages": messages},
                config=config,
                version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
    except Exception as e:
        yield f"[ERROR] {str(e)}"

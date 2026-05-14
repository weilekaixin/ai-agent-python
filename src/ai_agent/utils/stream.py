from collections.abc import AsyncGenerator

from langchain_core.messages import HumanMessage


async def token_stream(agent, message: str) -> AsyncGenerator[str, None]:
    try:
        async for event in agent.astream_events(
                {"messages": [HumanMessage(content=message)]},
                version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
    except Exception as e:
        yield f"[ERROR] {str(e)}"

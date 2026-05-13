from typing import AsyncGenerator


async def sse_format(gen: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    """把 agent 流式输出包装成 SSE 格式"""
    async for token in gen:
        yield f"data: {token}\n\n"

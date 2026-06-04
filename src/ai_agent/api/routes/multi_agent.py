import asyncio
from uuid import uuid4

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from ai_agent.core.supervisor import get_supervisor_graph
from ai_agent.models.constants import TEXT_EVENT_STREAM, HUMAN, AI
from ai_agent.modules.cache.history import save_message_to_redis
from ai_agent.modules.db.dao import save_message_to_db
from ai_agent.modules.memory.auto_memory import consolidate_conversation
from ai_agent.utils.sse import sse_format

router = APIRouter()


class MultiAgentRequest(BaseModel):
    """多智能体协作对话请求"""
    session_id: str = Field(..., min_length=1, max_length=36)
    message: str = Field(..., min_length=1, max_length=4000)


async def _token_stream(graph, message: str, config: dict):
    """Stream tokens from supervisor graph, skipping supervisor routing tokens."""
    try:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                # Skip one-word routing decision from supervisor node
                if event.get("metadata", {}).get("langgraph_node") == "supervisor":
                    continue
                content = event["data"]["chunk"].content
                if content:
                    yield content
    except Exception as e:
        yield f"[ERROR] {str(e)}"


@router.post("/multi-agent/chat", tags=["ai"])
async def multi_agent_chat(body: MultiAgentRequest):
    """多智能体协作对话接口。

    Supervisor 自动分析用户意图并路由到对应专家智能体：
    - **researcher**: 深度研究、联网搜索、信息汇总
    - **coder**: 代码编写、执行、调试
    - **general**: 普通对话、问答、写作
    """
    graph = get_supervisor_graph()
    config: dict = {"configurable": {}}

    async def stream_and_save():
        ai_parts: list[str] = []
        async for token in _token_stream(graph, body.message, config):
            ai_parts.append(token)
            yield token

        full_response = "".join(ai_parts)
        if full_response:
            save_message_to_redis(body.session_id, HUMAN, body.message)
            save_message_to_redis(body.session_id, AI, full_response)
            save_message_to_db(body.session_id, HUMAN, body.message)
            save_message_to_db(body.session_id, AI, full_response)

    return StreamingResponse(sse_format(stream_and_save()), media_type=TEXT_EVENT_STREAM)

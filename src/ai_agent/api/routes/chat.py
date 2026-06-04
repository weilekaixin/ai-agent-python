import json
from uuid import uuid4

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from ai_agent.api.schemas.chat import ChatRequest, ResumeRequest
from ai_agent.api.schemas.common import fail
from ai_agent.core.factory import build_messages_with_history
from ai_agent.models.constants import TEXT_EVENT_STREAM, ERROR_MESSAGE_AGENT_NOT_INIT, EMPTY_STR, AI, HUMAN
from ai_agent.modules.cache.history import save_message_to_redis
from ai_agent.modules.db.dao import save_message_to_db
from ai_agent.utils.sse import sse_format
from ai_agent.utils.stream import token_stream

router = APIRouter()


@router.post("/chat")
async def chat(query: Request, body: ChatRequest):
    agent = query.app.state.agent
    if agent is None:
        return fail(status.HTTP_503_SERVICE_UNAVAILABLE, ERROR_MESSAGE_AGENT_NOT_INIT,
                    status.HTTP_503_SERVICE_UNAVAILABLE)

    # 每次对话生成唯一 thread_id，与 session_id 解耦
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    messages = build_messages_with_history(body.session_id, body.message)

    async def stream_and_save():
        ai_response = []
        async for token in token_stream(agent, messages, config):
            ai_response.append(token)
            yield token

        state = await agent.aget_state(config)
        if state.next:  # next 不为空说明在等待人工审批
            last_message = state.values["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                tool_call = last_message.tool_calls[0]
                interrupt_data = {
                    "type": "interrupt",
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "tool_call_id": tool_call["id"],
                    "thread_id": thread_id,  # 前端调 /resume 时需要带回
                }
                yield f"__INTERRUPT__:{json.dumps(interrupt_data, ensure_ascii=False)}"
            return  # 暂停时不保存历史，等 resume 完成后再保存

        full_response = EMPTY_STR.join(ai_response)
        save_message_to_redis(body.session_id, HUMAN, body.message)
        save_message_to_redis(body.session_id, AI, full_response)
        save_message_to_db(body.session_id, HUMAN, body.message)
        save_message_to_db(body.session_id, AI, full_response)

    return StreamingResponse(sse_format(stream_and_save()), media_type=TEXT_EVENT_STREAM)


@router.post("/resume")
async def resume(query: Request, body: ResumeRequest):
    agent = query.app.state.agent
    if agent is None:
        return fail(status.HTTP_503_SERVICE_UNAVAILABLE, ERROR_MESSAGE_AGENT_NOT_INIT,
                    status.HTTP_503_SERVICE_UNAVAILABLE)

    config = {"configurable": {"thread_id": body.thread_id}}

    if not body.approved:
        try:
            state = await agent.aget_state(config)
            if state.next:
                async for _ in agent.astream_events(None, config, version="v2"):
                    pass
        except Exception:
            pass
        try:
            await agent.checkpointer.adelete_thread(body.thread_id)
        except Exception:
            pass

        async def cancel_response():
            yield "操作已取消"

        return StreamingResponse(sse_format(cancel_response()), media_type=TEXT_EVENT_STREAM)

    async def stream_and_save():
        ai_response = []
        async for token in token_stream(agent, None, config):
            ai_response.append(token)
            yield token

        full_response = EMPTY_STR.join(ai_response)
        full_state = await agent.aget_state(config)
        raw = next(
            msg.content for msg in full_state.values["messages"]
            if isinstance(msg, HumanMessage)
        )
        user_message = raw if isinstance(raw, str) else str(raw)

        save_message_to_redis(body.session_id, HUMAN, user_message)
        save_message_to_redis(body.session_id, AI, full_response)
        save_message_to_db(body.session_id, HUMAN, user_message)
        save_message_to_db(body.session_id, AI, full_response)

    async def stream_and_save_with_cleanup():
        try:
            async for token in stream_and_save():
                yield token
        finally:
            try:
                await agent.checkpointer.adelete_thread(body.thread_id)
            except Exception:
                pass

    return StreamingResponse(sse_format(stream_and_save_with_cleanup()), media_type=TEXT_EVENT_STREAM)

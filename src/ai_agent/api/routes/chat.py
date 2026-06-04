import asyncio
import json
from uuid import uuid4

from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage

from ai_agent.api.schemas.chat import ChatRequest, ResumeRequest
from ai_agent.api.schemas.common import fail
from ai_agent.core.factory import build_messages_with_history
from ai_agent.models.constants import TEXT_EVENT_STREAM, ERROR_MESSAGE_AGENT_NOT_INIT, EMPTY_STR, AI, HUMAN
from ai_agent.modules.cache.history import save_message_to_redis
from ai_agent.modules.db.dao import save_message_to_db, get_persona, record_token_usage
from ai_agent.modules.memory.auto_memory import consolidate_conversation
from ai_agent.utils.sse import sse_format
from ai_agent.utils.stream import token_stream

router = APIRouter()


def _record_tokens(session_id: str, messages: list) -> None:
    """Extract usage_metadata from the last AIMessage and persist to DB. No-op if absent."""
    last_ai = next(
        (m for m in reversed(messages) if getattr(m, "usage_metadata", None)),
        None,
    )
    if last_ai is None:
        return
    meta = last_ai.usage_metadata
    resp_meta = getattr(last_ai, "response_metadata", {}) or {}
    model_name = resp_meta.get("model_name") or resp_meta.get("model") or "unknown"
    record_token_usage(
        session_id=session_id,
        input_tokens=int(meta.get("input_tokens", 0)),
        output_tokens=int(meta.get("output_tokens", 0)),
        model=model_name,
    )


@router.post("/chat")
async def chat(query: Request, body: ChatRequest):
    agent = query.app.state.agent
    if agent is None:
        return fail(status.HTTP_503_SERVICE_UNAVAILABLE, ERROR_MESSAGE_AGENT_NOT_INIT,
                    status.HTTP_503_SERVICE_UNAVAILABLE)

    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    messages = build_messages_with_history(body.session_id, body.message)

    # Inject persona system prompt if provided (ChatGPT Custom GPTs style)
    if body.persona_id:
        persona = get_persona(body.persona_id)
        if persona and persona.get("system_prompt") and persona.get("is_active"):
            messages = [SystemMessage(content=persona["system_prompt"])] + messages

    async def stream_and_save():
        ai_response = []
        async for token in token_stream(agent, messages, config):
            ai_response.append(token)
            yield token

        state = await agent.aget_state(config)
        if state.next:
            last_message = state.values["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                tool_call = last_message.tool_calls[0]
                interrupt_data = {
                    "type": "interrupt",
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "tool_call_id": tool_call["id"],
                    "thread_id": thread_id,
                }
                yield f"__INTERRUPT__:{json.dumps(interrupt_data, ensure_ascii=False)}"
            return

        full_response = EMPTY_STR.join(ai_response)
        save_message_to_redis(body.session_id, HUMAN, body.message)
        save_message_to_redis(body.session_id, AI, full_response)
        save_message_to_db(body.session_id, HUMAN, body.message)
        save_message_to_db(body.session_id, AI, full_response)
        _record_tokens(body.session_id, state.values.get("messages", []))
        asyncio.create_task(consolidate_conversation(list(state.values["messages"])))

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
        _record_tokens(body.session_id, full_state.values.get("messages", []))
        asyncio.create_task(consolidate_conversation(list(full_state.values["messages"])))

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

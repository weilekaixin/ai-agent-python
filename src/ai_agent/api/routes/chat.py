from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse

from ai_agent.api.schemas.chat import ChatRequest
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
    retriever = query.app.state.retriever
    if agent is None:
        return fail(status.HTTP_503_SERVICE_UNAVAILABLE, ERROR_MESSAGE_AGENT_NOT_INIT,
                    status.HTTP_503_SERVICE_UNAVAILABLE)
    messages = build_messages_with_history(body.session_id, body.message, retriever)
    config = {"configurable": {"thread_id": body.session_id}}

    async def stream_and_save():
        ai_response = []
        async for token in token_stream(agent, messages, config):
            ai_response.append(token)
            yield token
        # 检查是否暂停（要调工具等审批）
        state = await agent.aget_state(config)
        if state.next:  # next 不为空说明在等待恢复
            # 获取最后一条 AI 消息的 tool_calls
            last_message = state.values["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                tool_call = last_message.tool_calls[0]
                import json
                interrupt_data = {
                    "type": "interrupt",
                    "tool": tool_call["name"],
                    "args": tool_call["args"],
                    "tool_call_id": tool_call["id"]
                }
                yield f"__INTERRUPT__:{json.dumps(interrupt_data, ensure_ascii=False)}"
            return  # 暂停时不保存历史
        # 正常结束，保存历史
        full_response = EMPTY_STR.join(ai_response)
        save_message_to_redis(body.session_id, HUMAN, body.message)
        save_message_to_redis(body.session_id, AI, full_response)
        save_message_to_db(body.session_id, HUMAN, body.message)
        save_message_to_db(body.session_id, AI, full_response)

    return StreamingResponse(sse_format(stream_and_save()), media_type=TEXT_EVENT_STREAM)

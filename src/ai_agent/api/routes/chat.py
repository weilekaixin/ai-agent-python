from fastapi import APIRouter, Request, status
from fastapi.responses import StreamingResponse

from ai_agent.api.schemas.chat import ChatRequest, ResumeRequest
from ai_agent.api.schemas.common import fail
from ai_agent.core.factory import build_messages_with_history
from ai_agent.models.constants import TEXT_EVENT_STREAM, ERROR_MESSAGE_AGENT_NOT_INIT, EMPTY_STR, AI, HUMAN
from ai_agent.modules.cache.history import save_message_to_redis
from ai_agent.modules.db.dao import save_message_to_db
from ai_agent.utils.sse import sse_format
from ai_agent.utils.stream import token_stream
import json

router = APIRouter()


@router.post("/chat")
async def chat(query: Request, body: ChatRequest):
    agent = query.app.state.agent
    retriever = query.app.state.retriever
    if agent is None:
        return fail(status.HTTP_503_SERVICE_UNAVAILABLE, ERROR_MESSAGE_AGENT_NOT_INIT,
                    status.HTTP_503_SERVICE_UNAVAILABLE)
    # 清理上次残留的 checkpoint（防止 resume 的 finally 未执行完的竞态条件）
    config = {"configurable": {"thread_id": body.session_id}}
    try:
        state = await agent.aget_state(config)
        if state and state.values.get("messages"):
            await agent.checkpointer.adelete_thread(body.session_id)
    except Exception:
        pass
    messages = build_messages_with_history(body.session_id, body.message, retriever)

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


@router.post("/resume")
async def resume(query: Request, body: ResumeRequest):
    """恢复暂停的 Agent"""
    agent = query.app.state.agent
    if agent is None:
        return fail(status.HTTP_503_SERVICE_UNAVAILABLE, ERROR_MESSAGE_AGENT_NOT_INIT,
                    status.HTTP_503_SERVICE_UNAVAILABLE)

    config = {"configurable": {"thread_id": body.session_id}}

    # 如果拒绝
    if not body.approved:
        # 让 graph 继续执行完毕，清除 checkpoint 中的中断状态
        try:
            state = await agent.aget_state(config)
            if state.next:
                async for _ in agent.astream_events(None, config, version="v2"):
                    pass
        except Exception:
            pass
        # 清除 checkpoint，让下次 /chat 创建新 run
        try:
            await agent.checkpointer.adelete_thread(body.session_id)
        except Exception:
            pass

        async def cancel_response():
            yield "操作已取消"

        return StreamingResponse(sse_format(cancel_response()), media_type=TEXT_EVENT_STREAM)

    # 同意：继续执行
    async def stream_and_save():
        ai_response = []
        # 传入 None 让 LangGraph 从 checkpoint 恢复，保留中断时的 tool_calls
        async for token in token_stream(agent, None, config):
            ai_response.append(token)
            yield token

        # 保存完整历史
        full_response = EMPTY_STR.join(ai_response)
        full_state = await agent.aget_state(config)
        user_message = full_state.values["messages"][0].content  # 第一条是用户问题

        save_message_to_redis(body.session_id, HUMAN, user_message)
        save_message_to_redis(body.session_id, AI, full_response)
        save_message_to_db(body.session_id, HUMAN, user_message)
        save_message_to_db(body.session_id, AI, full_response)

    async def stream_and_save_with_cleanup():
        try:
            async for token in stream_and_save():
                yield token
        finally:
            # 清除 checkpoint，让下次 /chat 创建新 run
            try:
                await agent.checkpointer.adelete_thread(body.session_id)
            except Exception:
                pass

    return StreamingResponse(sse_format(stream_and_save_with_cleanup()), media_type=TEXT_EVENT_STREAM)

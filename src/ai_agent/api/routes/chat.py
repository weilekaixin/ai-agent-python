from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ai_agent.api.schemas.chat import ChatRequest
from ai_agent.api.schemas.common import fail
from ai_agent.core.factory import build_rag_message
from fastapi import status
from ai_agent.models.constants import TEXT_EVENT_STREAM, ERROR_MESSAGE_AGENT_NOT_INIT
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
    message = build_rag_message(retriever, body.message)
    return StreamingResponse(sse_format(token_stream(agent, message)), media_type=TEXT_EVENT_STREAM)

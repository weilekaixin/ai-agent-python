from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ai_agent.api.schemas.chat import ChatRequest
from ai_agent.api.schemas.common import fail
from ai_agent.models.constants import TEXT_EVENT_STREAM, HTTP_503, ERROR_MESSAGE_AGENT_NOT_INIT
from ai_agent.utils.sse import sse_format
from ai_agent.utils.stream import token_stream

router = APIRouter()


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    agent = request.app.state.agent
    if agent is None:
        return fail(HTTP_503, ERROR_MESSAGE_AGENT_NOT_INIT, HTTP_503)
    return StreamingResponse(sse_format(token_stream(agent, body.message)), media_type=TEXT_EVENT_STREAM)

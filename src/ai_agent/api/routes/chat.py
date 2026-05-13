from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from ai_agent.api.schemas.chat import ChatRequest
from ai_agent.utils.sse import sse_format

router = APIRouter()


@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    agent = request.app.state.agent
    return StreamingResponse(
        sse_format(agent.chat(body.message)),
        media_type="text/event-stream"
    )

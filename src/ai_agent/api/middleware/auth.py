import secrets
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ai_agent.config.settings import settings

# 可从任意层读取当前请求 ID
REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="")

# 不需鉴权的路径
_SKIP_AUTH = {"/health", "/docs", "/openapi.json", "/redoc", "/metrics"}


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-Id into context var and propagate it to response headers."""

    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        REQUEST_ID.set(rid)
        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Validate X-Api-Key when settings.api_key is non-empty.
    Empty api_key = open mode (dev / internal deployment).
    """

    async def dispatch(self, request: Request, call_next):
        # 开发模式或跳过路径，直接放行
        if not settings.api_key or request.url.path in _SKIP_AUTH:
            return await call_next(request)
        provided = request.headers.get("X-Api-Key", "")
        # secrets.compare_digest 防止时序攻击
        if not provided or not secrets.compare_digest(
            provided.encode(), settings.api_key.encode()
        ):
            return JSONResponse(
                {"code": 401, "message": "Invalid or missing API key"},
                status_code=401,
            )
        return await call_next(request)

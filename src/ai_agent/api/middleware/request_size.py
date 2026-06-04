from __future__ import annotations

import logging

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

_SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/metrics"}
_DEFAULT_MAX_KB = 512


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the configured limit.

    Checks the Content-Length header only; does not buffer the request body.
    Chunked/streaming requests without a Content-Length header are not blocked.
    """

    def __init__(self, app, max_kb: int = _DEFAULT_MAX_KB):
        super().__init__(app)
        self._max_bytes = max_kb * 1024

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self._max_bytes:
            logger.warning(
                "Request body too large: %s bytes (limit %d)",
                content_length,
                self._max_bytes,
            )
            return JSONResponse(
                {"code": 413, "message": "请求体过大，请检查上传内容大小"},
                status_code=413,
            )
        return await call_next(request)

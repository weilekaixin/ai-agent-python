from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """Inject X-Response-Time: <ms>ms header into every response.

    Placed as the outermost middleware so it covers the full pipeline
    including CORS, rate limiting, auth, and route handling.
    For SSE endpoints the time reflects connection establishment,
    not the full stream duration.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
        return response

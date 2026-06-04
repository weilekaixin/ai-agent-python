from __future__ import annotations

import asyncio
import logging

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ai_agent.modules.cache.client import get_redis_client

logger = logging.getLogger(__name__)

_SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/metrics"}

# path prefix → (max_requests, window_seconds)
_PATH_LIMITS: dict[str, tuple[int, int]] = {
    "/api/chat": (30, 60),
    "/api/multi-agent/chat": (10, 60),
    "/api/structured": (20, 60),
    "/api/dream": (5, 60),
}
_DEFAULT_LIMIT: tuple[int, int] = (60, 60)


def _client_key(request: Request) -> str:
    api_key = request.headers.get("X-Api-Key", "")
    if api_key:
        return f"key:{api_key[:8]}"  # bucket by key prefix, never log full key
    return f"ip:{request.client.host if request.client else 'unknown'}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self._enabled = enabled

    async def dispatch(self, request: Request, call_next):
        if not self._enabled or request.url.path in _SKIP_PATHS:
            return await call_next(request)

        path = request.url.path
        limit, window = _DEFAULT_LIMIT
        for prefix, limits in _PATH_LIMITS.items():
            if path.startswith(prefix):
                limit, window = limits
                break

        redis_key = f"ratelimit:{_client_key(request)}:{path}"

        try:
            loop = asyncio.get_event_loop()
            r = get_redis_client()
            count = await loop.run_in_executor(None, r.incr, redis_key)
            if count == 1:
                # Set TTL only on first request; subsequent incr calls don't reset it
                await loop.run_in_executor(None, r.expire, redis_key, window)
            if count > limit:
                ttl = await loop.run_in_executor(None, r.ttl, redis_key)
                return JSONResponse(
                    {"code": 429, "message": "请求过于频繁，请稍后再试"},
                    status_code=429,
                    headers={"Retry-After": str(max(ttl, 1))},
                )
        except Exception:
            # Fail open: Redis unavailable → skip rate limiting
            logger.warning("Rate limiter Redis error; skipping for %s", path)

        return await call_next(request)

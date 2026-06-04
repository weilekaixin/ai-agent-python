"""Optional JWT authentication middleware.

Activated when settings.jwt_enabled = True.
Validates Bearer tokens using PyJWT, extracts 'sub' claim,
and exposes it as request.state.user_id for downstream use.
"""
from __future__ import annotations

import logging

import jwt
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from ai_agent.config.settings import settings

logger = logging.getLogger(__name__)

_SKIP_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/metrics"}


class JwtAuthMiddleware(BaseHTTPMiddleware):
    """Validate Bearer JWT tokens when settings.jwt_enabled = True.

    On success: request.state.user_id is set from the 'sub' JWT claim.
    On failure: returns 401 with a structured error message.
    Skip paths bypass all JWT validation regardless of jwt_enabled.
    """

    async def dispatch(self, request: Request, call_next):
        request.state.user_id = None

        if not settings.jwt_enabled or request.url.path in _SKIP_PATHS:
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse(
                {"code": 401, "message": "Authorization header required (Bearer <token>)"},
                status_code=401,
            )

        token = auth[7:]
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            request.state.user_id = payload.get("sub")
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                {"code": 401, "message": "Token has expired"},
                status_code=401,
            )
        except jwt.InvalidTokenError as exc:
            logger.debug("JWT validation failed: %s", exc)
            return JSONResponse(
                {"code": 401, "message": "Invalid JWT token"},
                status_code=401,
            )

        return await call_next(request)

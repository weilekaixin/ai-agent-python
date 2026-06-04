"""
Unit tests for JwtAuthMiddleware.
All I/O is mocked — no database or network calls.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_SECRET = "test-secret-key-for-unit-tests"
_ALGO = "HS256"


def _make_token(sub: str = "user123", exp_delta_seconds: int = 300) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=exp_delta_seconds),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALGO)


def _make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/chat")
    async def chat():
        return {"ok": True}

    return app


def _client() -> TestClient:
    from ai_agent.api.middleware.jwt_auth import JwtAuthMiddleware
    app = _make_app()
    app.add_middleware(JwtAuthMiddleware)
    return TestClient(app, raise_server_exceptions=False)


class TestJwtAuthMiddleware:
    def test_disabled_passes_all_requests(self):
        client = _client()
        with patch("ai_agent.api.middleware.jwt_auth.settings") as m:
            m.jwt_enabled = False
            assert client.get("/api/chat").status_code == 200

    def test_health_path_never_requires_token(self):
        client = _client()
        with patch("ai_agent.api.middleware.jwt_auth.settings") as m:
            m.jwt_enabled = True
            m.jwt_secret = _SECRET
            m.jwt_algorithm = _ALGO
            assert client.get("/health").status_code == 200

    def test_valid_token_is_accepted(self):
        client = _client()
        token = _make_token()
        with patch("ai_agent.api.middleware.jwt_auth.settings") as m:
            m.jwt_enabled = True
            m.jwt_secret = _SECRET
            m.jwt_algorithm = _ALGO
            resp = client.get("/api/chat", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    def test_missing_bearer_returns_401(self):
        client = _client()
        with patch("ai_agent.api.middleware.jwt_auth.settings") as m:
            m.jwt_enabled = True
            m.jwt_secret = _SECRET
            m.jwt_algorithm = _ALGO
            resp = client.get("/api/chat")
        assert resp.status_code == 401
        assert resp.json()["code"] == 401

    def test_malformed_token_returns_401(self):
        client = _client()
        with patch("ai_agent.api.middleware.jwt_auth.settings") as m:
            m.jwt_enabled = True
            m.jwt_secret = _SECRET
            m.jwt_algorithm = _ALGO
            resp = client.get("/api/chat", headers={"Authorization": "Bearer not-a-jwt"})
        assert resp.status_code == 401

    def test_expired_token_returns_401_with_message(self):
        client = _client()
        expired = _make_token(exp_delta_seconds=-1)  # already expired
        with patch("ai_agent.api.middleware.jwt_auth.settings") as m:
            m.jwt_enabled = True
            m.jwt_secret = _SECRET
            m.jwt_algorithm = _ALGO
            resp = client.get("/api/chat", headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401
        assert "expired" in resp.json()["message"].lower()

    def test_wrong_secret_returns_401(self):
        client = _client()
        token = _make_token()  # signed with _SECRET
        with patch("ai_agent.api.middleware.jwt_auth.settings") as m:
            m.jwt_enabled = True
            m.jwt_secret = "completely-wrong-secret"
            m.jwt_algorithm = _ALGO
            resp = client.get("/api/chat", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

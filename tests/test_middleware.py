"""
Unit tests for API middleware: RequestIdMiddleware, ApiKeyMiddleware,
RateLimitMiddleware, and RequestSizeMiddleware.

All external I/O is mocked — no live Redis, database, or network required.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Shared test app factory
# ---------------------------------------------------------------------------

def _make_app() -> FastAPI:
    """Minimal FastAPI app with representative routes for middleware testing."""
    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/chat")
    async def chat_get():
        return {"ok": True}

    @app.post("/api/chat")
    async def chat_post(request: Request):
        return {"ok": True}

    @app.get("/api/multi-agent/chat")
    async def multi_agent():
        return {"ok": True}

    return app


# ---------------------------------------------------------------------------
# RequestIdMiddleware
# ---------------------------------------------------------------------------

class TestRequestIdMiddleware:
    def _client(self) -> TestClient:
        from ai_agent.api.middleware.auth import RequestIdMiddleware
        app = _make_app()
        app.add_middleware(RequestIdMiddleware)
        return TestClient(app)

    def test_request_id_added_to_response(self):
        resp = self._client().get("/health")
        assert "x-request-id" in resp.headers
        assert resp.headers["x-request-id"]  # non-empty

    def test_incoming_request_id_is_preserved(self):
        resp = self._client().get("/health", headers={"X-Request-Id": "fixed-id-42"})
        assert resp.headers["x-request-id"] == "fixed-id-42"

    def test_generated_id_is_valid_hex(self):
        rid = self._client().get("/health").headers["x-request-id"]
        assert len(rid) == 32
        int(rid, 16)  # raises ValueError if not valid hex


# ---------------------------------------------------------------------------
# ApiKeyMiddleware
# ---------------------------------------------------------------------------

class TestApiKeyMiddleware:
    def _client(self) -> TestClient:
        from ai_agent.api.middleware.auth import ApiKeyMiddleware
        app = _make_app()
        app.add_middleware(ApiKeyMiddleware)
        return TestClient(app, raise_server_exceptions=False)

    def test_open_mode_no_key_configured(self):
        client = self._client()
        with patch("ai_agent.api.middleware.auth.settings") as m:
            m.api_key = ""
            assert client.get("/api/chat").status_code == 200

    def test_valid_x_api_key_passes(self):
        client = self._client()
        with patch("ai_agent.api.middleware.auth.settings") as m:
            m.api_key = "my-secret"
            resp = client.get("/api/chat", headers={"X-Api-Key": "my-secret"})
            assert resp.status_code == 200

    def test_invalid_key_returns_401(self):
        client = self._client()
        with patch("ai_agent.api.middleware.auth.settings") as m:
            m.api_key = "my-secret"
            resp = client.get("/api/chat", headers={"X-Api-Key": "wrong"})
            assert resp.status_code == 401
            assert resp.json()["code"] == 401

    def test_missing_key_returns_401(self):
        client = self._client()
        with patch("ai_agent.api.middleware.auth.settings") as m:
            m.api_key = "my-secret"
            assert client.get("/api/chat").status_code == 401

    def test_health_bypasses_auth(self):
        client = self._client()
        with patch("ai_agent.api.middleware.auth.settings") as m:
            m.api_key = "my-secret"
            assert client.get("/health").status_code == 200

    def test_docs_path_bypasses_auth(self):
        from ai_agent.api.middleware.auth import ApiKeyMiddleware
        app = _make_app()

        @app.get("/docs")
        async def fake_docs():
            return {"page": "docs"}

        app.add_middleware(ApiKeyMiddleware)
        client = TestClient(app, raise_server_exceptions=False)
        with patch("ai_agent.api.middleware.auth.settings") as m:
            m.api_key = "my-secret"
            assert client.get("/docs").status_code == 200


# ---------------------------------------------------------------------------
# RateLimitMiddleware
# ---------------------------------------------------------------------------

class TestRateLimitMiddleware:
    def _client(self, enabled: bool = True) -> TestClient:
        from ai_agent.api.middleware.rate_limit import RateLimitMiddleware
        app = _make_app()
        app.add_middleware(RateLimitMiddleware, enabled=enabled)
        return TestClient(app, raise_server_exceptions=False)

    def test_disabled_allows_all_requests(self):
        client = self._client(enabled=False)
        for _ in range(50):
            assert client.get("/api/chat").status_code == 200

    def test_health_path_not_counted(self):
        mock_r = MagicMock()
        client = self._client(enabled=True)
        with patch("ai_agent.api.middleware.rate_limit.get_redis_client", return_value=mock_r):
            client.get("/health")
        mock_r.incr.assert_not_called()

    def test_within_limit_passes(self):
        mock_r = MagicMock()
        mock_r.incr.return_value = 5  # well within 30/min
        client = self._client(enabled=True)
        with patch("ai_agent.api.middleware.rate_limit.get_redis_client", return_value=mock_r):
            assert client.get("/api/chat").status_code == 200

    def test_exceeded_limit_returns_429(self):
        mock_r = MagicMock()
        mock_r.incr.return_value = 99999
        mock_r.ttl.return_value = 45
        client = self._client(enabled=True)
        with patch("ai_agent.api.middleware.rate_limit.get_redis_client", return_value=mock_r):
            resp = client.get("/api/chat")
        assert resp.status_code == 429
        assert resp.json()["code"] == 429
        assert "retry-after" in resp.headers

    def test_first_request_sets_expiry(self):
        mock_r = MagicMock()
        mock_r.incr.return_value = 1
        client = self._client(enabled=True)
        with patch("ai_agent.api.middleware.rate_limit.get_redis_client", return_value=mock_r):
            client.get("/api/chat")
        mock_r.expire.assert_called_once()

    def test_subsequent_requests_skip_expiry(self):
        mock_r = MagicMock()
        mock_r.incr.return_value = 2  # not the first request
        client = self._client(enabled=True)
        with patch("ai_agent.api.middleware.rate_limit.get_redis_client", return_value=mock_r):
            client.get("/api/chat")
        mock_r.expire.assert_not_called()

    def test_fail_open_on_redis_error(self):
        mock_r = MagicMock()
        mock_r.incr.side_effect = ConnectionError("Redis down")
        client = self._client(enabled=True)
        with patch("ai_agent.api.middleware.rate_limit.get_redis_client", return_value=mock_r):
            resp = client.get("/api/chat")
        assert resp.status_code == 200  # fail-open: never block on Redis error

    def test_multi_agent_tighter_limit(self):
        """multi-agent/chat has limit 10/min; count=11 should return 429."""
        mock_r = MagicMock()
        mock_r.incr.return_value = 11
        mock_r.ttl.return_value = 30
        client = self._client(enabled=True)
        with patch("ai_agent.api.middleware.rate_limit.get_redis_client", return_value=mock_r):
            resp = client.get("/api/multi-agent/chat")
        assert resp.status_code == 429


# ---------------------------------------------------------------------------
# RequestSizeMiddleware
# ---------------------------------------------------------------------------

class TestRequestSizeMiddleware:
    def _client(self, max_kb: int) -> TestClient:
        from ai_agent.api.middleware.request_size import RequestSizeMiddleware
        app = _make_app()
        app.add_middleware(RequestSizeMiddleware, max_kb=max_kb)
        return TestClient(app, raise_server_exceptions=False)

    def test_small_body_passes(self):
        resp = self._client(max_kb=10).post(
            "/api/chat",
            content=b"x" * 100,
            headers={"Content-Type": "text/plain"},
        )
        assert resp.status_code == 200

    def test_oversized_body_rejected(self):
        payload = b"x" * 2048  # 2 KB > 1 KB limit
        resp = self._client(max_kb=1).post(
            "/api/chat",
            content=payload,
            headers={"Content-Type": "text/plain"},
        )
        assert resp.status_code == 413
        assert resp.json()["code"] == 413

    def test_health_skips_size_check(self):
        assert self._client(max_kb=1).get("/health").status_code == 200

    def test_no_content_length_passes(self):
        """GET requests have no body; should never be blocked."""
        assert self._client(max_kb=1).get("/api/chat").status_code == 200

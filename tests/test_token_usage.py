"""Tests for token usage tracking."""
from unittest.mock import MagicMock, patch


def _make_mock_session():
    ms = MagicMock()
    ms.__enter__ = MagicMock(return_value=ms)
    ms.__exit__ = MagicMock(return_value=False)
    return ms


def test_record_token_usage_inserts_row():
    from ai_agent.modules.db.dao import record_token_usage
    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        mock_ctx.return_value = ms
        record_token_usage("s1", 100, 50, "gpt-4o")
        ms.add.assert_called_once()
        added = ms.add.call_args[0][0]
        assert added.input_tokens == 100
        assert added.output_tokens == 50
        assert added.total_tokens == 150
        assert added.model == "gpt-4o"


def test_get_token_usage_summary_empty():
    from ai_agent.modules.db.dao import get_token_usage_summary
    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        ms.exec.return_value.all.return_value = []
        mock_ctx.return_value = ms
        s = get_token_usage_summary("s1")
        assert s["requests"] == 0
        assert s["total_tokens"] == 0
        assert s["total_input_tokens"] == 0
        assert s["total_output_tokens"] == 0


def test_get_token_usage_summary_calculation():
    from ai_agent.modules.db.models import TokenUsage
    from ai_agent.modules.db.dao import get_token_usage_summary

    u1 = TokenUsage(session_id="s1", input_tokens=100, output_tokens=50, total_tokens=150, model="gpt-4o")
    u2 = TokenUsage(session_id="s1", input_tokens=200, output_tokens=100, total_tokens=300, model="gpt-4o")

    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        ms.exec.return_value.all.return_value = [u1, u2]
        mock_ctx.return_value = ms
        s = get_token_usage_summary("s1")

    assert s["requests"] == 2
    assert s["total_input_tokens"] == 300
    assert s["total_output_tokens"] == 150
    assert s["total_tokens"] == 450


def test_record_tokens_no_op_when_no_usage_metadata():
    """_record_tokens should not raise if no message has usage_metadata."""
    from ai_agent.api.routes.chat import _record_tokens
    from unittest.mock import MagicMock

    msg = MagicMock(spec=[])  # no usage_metadata attribute
    # Should not raise and not attempt any DB write
    with patch("ai_agent.api.routes.chat.record_token_usage") as mock_record:
        _record_tokens("s1", [msg])
        mock_record.assert_not_called()


def test_record_tokens_extracts_metadata():
    from ai_agent.api.routes.chat import _record_tokens

    msg = MagicMock()
    msg.usage_metadata = {"input_tokens": 80, "output_tokens": 40}
    msg.response_metadata = {"model_name": "claude-sonnet-4-6"}

    with patch("ai_agent.api.routes.chat.record_token_usage") as mock_record:
        _record_tokens("sess-x", [msg])
        mock_record.assert_called_once_with(
            session_id="sess-x",
            input_tokens=80,
            output_tokens=40,
            model="claude-sonnet-4-6",
        )


def test_usage_router_paths():
    from ai_agent.api.routes.usage import router
    paths = {r.path for r in router.routes}
    assert "/sessions/{session_id}/usage" in paths
    assert "/sessions/{session_id}/usage/summary" in paths

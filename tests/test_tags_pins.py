"""Tests for session tags and message pinning."""
import pytest
from unittest.mock import MagicMock, patch


# ── Tag DAO unit tests ───────────────────────────────────────────────────

def _make_mock_session():
    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)
    return mock_session


def test_get_session_tags_empty():
    from ai_agent.modules.db.dao import get_session_tags
    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        ms.exec.return_value.all.return_value = []
        mock_ctx.return_value = ms
        assert get_session_tags("s1") == []


def test_list_all_tags_empty():
    from ai_agent.modules.db.dao import list_all_tags
    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        ms.exec.return_value.all.return_value = []
        mock_ctx.return_value = ms
        assert list_all_tags() == []


def test_list_all_tags_counts():
    from ai_agent.modules.db.dao import list_all_tags
    from ai_agent.modules.db.models import SessionTag

    t1 = SessionTag(session_id="s1", tag="work")
    t2 = SessionTag(session_id="s2", tag="work")
    t3 = SessionTag(session_id="s1", tag="personal")

    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        ms.exec.return_value.all.return_value = [t1, t2, t3]
        mock_ctx.return_value = ms
        result = list_all_tags()

    assert result[0] == {"tag": "work", "count": 2}
    assert result[1] == {"tag": "personal", "count": 1}


def test_get_sessions_by_tag_returns_ids():
    from ai_agent.modules.db.dao import get_sessions_by_tag
    from ai_agent.modules.db.models import SessionTag

    t1 = SessionTag(session_id="s1", tag="ai")
    t2 = SessionTag(session_id="s2", tag="ai")

    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        # first exec = count query, second = data query
        ms.exec.return_value.one.return_value = 2
        ms.exec.return_value.all.return_value = [t1, t2]
        mock_ctx.return_value = ms
        ids, total = get_sessions_by_tag("ai")

    assert total == 2
    assert "s1" in ids
    assert "s2" in ids


# ── Pin DAO unit tests ───────────────────────────────────────────────────

def test_get_pinned_messages_empty():
    from ai_agent.modules.db.dao import get_pinned_messages
    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        ms.exec.return_value.all.return_value = []
        mock_ctx.return_value = ms
        assert get_pinned_messages("s1") == []


def test_unpin_nonexistent_returns_false():
    from ai_agent.modules.db.dao import unpin_message
    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        ms = _make_mock_session()
        ms.exec.return_value.first.return_value = None
        mock_ctx.return_value = ms
        assert unpin_message(999999) is False


# ── Route registration smoke tests ────────────────────────────────────────

def test_tags_router_paths():
    from ai_agent.api.routes.tags import router
    paths = {r.path for r in router.routes}
    assert "/sessions/{session_id}/tags" in paths
    assert "/sessions/{session_id}/tags/{tag}" in paths
    assert "/tags" in paths
    assert "/tags/{tag}/sessions" in paths


def test_message_router_paths():
    from ai_agent.api.routes.message import router
    paths = {r.path for r in router.routes}
    assert "/messages/{message_id}/pin" in paths
    assert "/sessions/{session_id}/pinned" in paths

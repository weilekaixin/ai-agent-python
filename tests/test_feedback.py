"""Tests for the message feedback endpoints."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ── unit-level tests (no DB / LLM required) ──────────────────────────────────

def test_feedback_schema_valid_thumbs_up():
    from ai_agent.api.schemas.feedback import FeedbackCreate
    fb = FeedbackCreate(rating=1)
    assert fb.rating == 1
    assert fb.comment is None


def test_feedback_schema_valid_thumbs_down_with_comment():
    from ai_agent.api.schemas.feedback import FeedbackCreate
    fb = FeedbackCreate(rating=-1, comment="not helpful")
    assert fb.rating == -1
    assert fb.comment == "not helpful"


def test_feedback_schema_invalid_rating_zero():
    from pydantic import ValidationError
    from ai_agent.api.schemas.feedback import FeedbackCreate
    with pytest.raises(ValidationError):
        FeedbackCreate(rating=0)


def test_feedback_schema_invalid_rating_two():
    from pydantic import ValidationError
    from ai_agent.api.schemas.feedback import FeedbackCreate
    with pytest.raises(ValidationError):
        FeedbackCreate(rating=2)


def test_feedback_schema_missing_rating():
    from pydantic import ValidationError
    from ai_agent.api.schemas.feedback import FeedbackCreate
    with pytest.raises(ValidationError):
        FeedbackCreate()


# ── DAO-level unit tests (mocked DB) ─────────────────────────────────────────

def test_get_feedback_stats_empty_session():
    from ai_agent.modules.db.dao import get_feedback_stats
    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.exec.return_value.all.return_value = []
        mock_ctx.return_value = mock_session

        stats = get_feedback_stats("no-such-session")
        assert stats["total"] == 0
        assert stats["positive"] == 0
        assert stats["negative"] == 0
        assert stats["positive_rate"] == 0.0


def test_get_feedback_stats_calculation():
    from ai_agent.modules.db.models import MessageFeedback
    from ai_agent.modules.db.dao import get_feedback_stats

    fb1 = MessageFeedback(feedback_id="a", message_id=1, session_id="s1", rating=1)
    fb2 = MessageFeedback(feedback_id="b", message_id=2, session_id="s1", rating=1)
    fb3 = MessageFeedback(feedback_id="c", message_id=3, session_id="s1", rating=-1)

    with patch("ai_agent.modules.db.dao.get_session") as mock_ctx:
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session.exec.return_value.all.return_value = [fb1, fb2, fb3]
        mock_ctx.return_value = mock_session

        stats = get_feedback_stats("s1")
        assert stats["total"] == 3
        assert stats["positive"] == 2
        assert stats["negative"] == 1
        assert stats["positive_rate"] == round(2 / 3, 4)


def test_feedback_router_registered():
    """Smoke test: feedback router endpoints appear in the OpenAPI schema."""
    from ai_agent.api.routes.feedback import router
    paths = {r.path for r in router.routes}
    assert "/messages/{message_id}/feedback" in paths
    assert "/sessions/{session_id}/feedback" in paths
    assert "/sessions/{session_id}/feedback/stats" in paths

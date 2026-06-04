"""Unit tests for Pydantic schema validation — no I/O required."""
import pytest
from pydantic import ValidationError

from ai_agent.api.schemas.chat import ChatRequest, ResumeRequest
from ai_agent.api.schemas.persona import PersonaCreate, PersonaUpdate


# ──────────── ChatRequest ────────────

def test_chat_request_valid():
    r = ChatRequest(session_id="sess-1", message="hello")
    assert r.session_id == "sess-1"
    assert r.persona_id is None


def test_chat_request_with_persona():
    r = ChatRequest(session_id="sess-1", message="hi", persona_id="abc123")
    assert r.persona_id == "abc123"


def test_chat_request_empty_message_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(session_id="sess-1", message="")


def test_chat_request_message_too_long_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(session_id="sess-1", message="x" * 4001)


def test_chat_request_empty_session_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(session_id="", message="hello")


# ──────────── ResumeRequest ────────────

def test_resume_request_valid():
    r = ResumeRequest(session_id="s1", thread_id="t1", approved=True)
    assert r.approved is True


def test_resume_request_deny():
    r = ResumeRequest(session_id="s1", thread_id="t1", approved=False)
    assert r.approved is False


# ──────────── PersonaCreate ────────────

def test_persona_create_minimal():
    p = PersonaCreate(name="Bot", system_prompt="You are a bot.")
    assert p.description is None
    assert p.avatar is None


def test_persona_create_full():
    p = PersonaCreate(
        name="Analyst",
        system_prompt="You are a data analyst.",
        description="Helps with data",
        avatar="https://example.com/avatar.png",
    )
    assert p.description == "Helps with data"


def test_persona_create_name_too_long_rejected():
    with pytest.raises(ValidationError):
        PersonaCreate(name="x" * 101, system_prompt="test")


# ──────────── PersonaUpdate ────────────

def test_persona_update_disable():
    u = PersonaUpdate(is_active=False)
    assert u.is_active is False
    assert u.name is None  # other fields untouched


def test_persona_update_all_optional():
    u = PersonaUpdate()  # all fields optional
    assert u.name is None
    assert u.is_active is None

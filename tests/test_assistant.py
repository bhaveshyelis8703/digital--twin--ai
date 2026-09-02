"""
tests/test_assistant.py

Milestone 4 tests for the Conversational AI assistant.
All LLM calls are mocked — tests run without an OpenAI key.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
_ROOT    = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def auth_headers(client):
    """Register + login, return Bearer headers."""
    client.post("/api/auth/register", json={
        "name": "Chat Tester", "email": "chat@test.com",
        "password": "chat1234!", "age": 28, "occupation": "Dev",
    })
    r = client.post("/api/auth/login",
                    data={"username": "chat@test.com", "password": "chat1234!"})
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────────────────────────────────────
# SAFETY FILTER
# ─────────────────────────────────────────────────────────────────────────────

class TestSafetyFilter:
    def test_gambling_message_is_unsafe(self):
        from app.services.conversational_ai import _is_unsafe
        assert _is_unsafe("Should I borrow money to gamble?")

    def test_normal_message_is_safe(self):
        from app.services.conversational_ai import _is_unsafe
        assert not _is_unsafe("How can I increase my savings rate?")

    def test_casino_pattern_blocked(self):
        from app.services.conversational_ai import _is_unsafe
        assert _is_unsafe("I want to go to the casino and invest there")

    def test_tax_evasion_blocked(self):
        from app.services.conversational_ai import _is_unsafe
        assert _is_unsafe("How do I hide income for tax evasion?")

    def test_normal_investment_allowed(self):
        from app.services.conversational_ai import _is_unsafe
        assert not _is_unsafe("What if I invest 10% of my income in index funds?")

    def test_savings_question_allowed(self):
        from app.services.conversational_ai import _is_unsafe
        assert not _is_unsafe("Will I save $50K in 3 years?")


# ─────────────────────────────────────────────────────────────────────────────
# INTENT CLASSIFIER
# ─────────────────────────────────────────────────────────────────────────────

class TestIntentClassifier:
    def _classify(self, msg):
        from app.services.conversational_ai import classify_intent
        return classify_intent(msg)

    def test_forecast_intent(self):
        assert self._classify("How much will I save next year?") == "forecast"

    def test_forecast_intent_will_i(self):
        assert self._classify("Will I be able to save $50K in 3 years?") == "forecast"

    def test_simulate_intent(self):
        assert self._classify("What if I invest 10% of my income?") == "simulate"

    def test_simulate_what_if(self):
        assert self._classify("What if I cut my expenses by 20%?") == "simulate"

    def test_advice_intent(self):
        assert self._classify("How can I improve my savings?") == "advice"

    def test_advice_should_i(self):
        assert self._classify("Should I open a new savings account?") == "advice"

    def test_explain_intent(self):
        assert self._classify("Why did my productivity score decrease?") == "explain"

    def test_explain_what_is(self):
        assert self._classify("What is a savings rate?") in ("explain", "general")

    def test_general_fallback(self):
        assert self._classify("Hello how are you") == "general"


# ─────────────────────────────────────────────────────────────────────────────
# CONVERSATION MEMORY
# ─────────────────────────────────────────────────────────────────────────────

class TestConversationMemory:
    def test_add_and_get_memory(self):
        from app.services.conversational_ai import add_to_memory, get_memory, clear_memory
        cid = str(uuid.uuid4())
        add_to_memory(cid, "user", "hello")
        add_to_memory(cid, "assistant", "hi there")
        mem = get_memory(cid)
        assert len(mem) == 2
        assert mem[0]["role"] == "user"
        assert mem[1]["role"] == "assistant"
        clear_memory(cid)

    def test_memory_window_trimming(self):
        from app.services.conversational_ai import add_to_memory, get_memory, clear_memory, _MEMORY_MAX_TURNS
        cid = str(uuid.uuid4())
        # Add more than the window allows
        for i in range(_MEMORY_MAX_TURNS + 5):
            add_to_memory(cid, "user", f"msg {i}")
            add_to_memory(cid, "assistant", f"resp {i}")
        mem = get_memory(cid)
        assert len(mem) <= _MEMORY_MAX_TURNS * 2
        clear_memory(cid)

    def test_clear_memory(self):
        from app.services.conversational_ai import add_to_memory, get_memory, clear_memory
        cid = str(uuid.uuid4())
        add_to_memory(cid, "user", "test")
        clear_memory(cid)
        assert get_memory(cid) == []

    def test_separate_conversations(self):
        from app.services.conversational_ai import add_to_memory, get_memory, clear_memory
        cid1, cid2 = str(uuid.uuid4()), str(uuid.uuid4())
        add_to_memory(cid1, "user", "conv1")
        add_to_memory(cid2, "user", "conv2")
        assert len(get_memory(cid1)) == 1
        assert len(get_memory(cid2)) == 1
        assert get_memory(cid1)[0]["content"] == "conv1"
        clear_memory(cid1)
        clear_memory(cid2)


# ─────────────────────────────────────────────────────────────────────────────
# CHAT API ENDPOINT (no OpenAI key — uses fallback)
# ─────────────────────────────────────────────────────────────────────────────

class TestChatEndpoint:
    def test_chat_requires_auth(self, client):
        r = client.post("/api/assistant/chat",
                        json={"message": "hello", "conversation_id": None})
        assert r.status_code == 401

    def test_chat_returns_response(self, client, auth_headers):
        """Without API key, fallback response is returned."""
        cid = str(uuid.uuid4())
        r = client.post(
            "/api/assistant/chat",
            json={"message": "How much will I save?", "conversation_id": cid},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "response" in body
        assert "conversation_id" in body
        assert len(body["response"]) > 0
        assert body["conversation_id"] == cid

    def test_chat_generates_conv_id_if_none(self, client, auth_headers):
        r = client.post(
            "/api/assistant/chat",
            json={"message": "hello"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert len(r.json()["conversation_id"]) == 36  # UUID format

    def test_chat_safety_refusal(self, client, auth_headers):
        r = client.post(
            "/api/assistant/chat",
            json={"message": "Should I borrow money to gamble at the casino?"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "risk" in body["response"].lower() or "harmful" in body["response"].lower() \
               or "gambl" in body["response"].lower() or "safer" in body["response"].lower()

    def test_chat_empty_message_rejected(self, client, auth_headers):
        r = client.post(
            "/api/assistant/chat",
            json={"message": ""},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_message_too_long_rejected(self, client, auth_headers):
        r = client.post(
            "/api/assistant/chat",
            json={"message": "x" * 5000},
            headers=auth_headers,
        )
        assert r.status_code == 422

    def test_intent_in_response(self, client, auth_headers):
        r = client.post(
            "/api/assistant/chat",
            json={"message": "What if I save 20% more per month?"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json().get("intent") in (
            "simulate", "forecast", "advice", "explain", "general", "refused"
        )

    def test_streaming_fallback_returns_text(self, client, auth_headers):
        r = client.post(
            "/api/assistant/chat",
            json={"message": "hello", "stream": True},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.text


# ─────────────────────────────────────────────────────────────────────────────
# CONVERSATION HISTORY API
# ─────────────────────────────────────────────────────────────────────────────

class TestHistoryEndpoint:
    def _send(self, client, headers, msg, cid):
        return client.post(
            "/api/assistant/chat",
            json={"message": msg, "conversation_id": cid},
            headers=headers,
        )

    def test_history_empty_for_new_conv(self, client, auth_headers):
        cid = str(uuid.uuid4())
        r = client.get(f"/api/assistant/history/{cid}", headers=auth_headers)
        assert r.status_code == 200
        assert r.json() == []

    def test_history_populated_after_chat(self, client, auth_headers):
        cid = str(uuid.uuid4())
        self._send(client, auth_headers, "test message", cid)
        r = client.get(f"/api/assistant/history/{cid}", headers=auth_headers)
        assert r.status_code == 200
        msgs = r.json()
        assert len(msgs) >= 2
        roles = [m["role"] for m in msgs]
        assert "user" in roles
        assert "assistant" in roles

    def test_history_owned_by_user(self, client, auth_headers):
        """Another user cannot access this user's history."""
        cid = str(uuid.uuid4())
        self._send(client, auth_headers, "private message", cid)

        # Register second user
        client.post("/api/auth/register", json={
            "name": "Other", "email": "other@test.com",
            "password": "other1234!", "age": 25, "occupation": "X",
        })
        r2 = client.post("/api/auth/login",
                         data={"username": "other@test.com", "password": "other1234!"})
        other_headers = {"Authorization": f"Bearer {r2.json()['access_token']}"}

        r = client.get(f"/api/assistant/history/{cid}", headers=other_headers)
        assert r.status_code == 200
        assert r.json() == []  # IDOR: returns empty, not 200 with data

    def test_delete_conversation(self, client, auth_headers):
        cid = str(uuid.uuid4())
        self._send(client, auth_headers, "to be deleted", cid)
        # Verify it exists
        r1 = client.get(f"/api/assistant/history/{cid}", headers=auth_headers)
        assert len(r1.json()) > 0
        # Delete
        r2 = client.delete(f"/api/assistant/history/{cid}", headers=auth_headers)
        assert r2.status_code == 204
        # Verify gone
        r3 = client.get(f"/api/assistant/history/{cid}", headers=auth_headers)
        assert r3.json() == []

    def test_delete_nonexistent_conversation_404(self, client, auth_headers):
        cid = str(uuid.uuid4())
        r = client.delete(f"/api/assistant/history/{cid}", headers=auth_headers)
        assert r.status_code == 404

    def test_list_conversations(self, client, auth_headers):
        cid = str(uuid.uuid4())
        self._send(client, auth_headers, "list test", cid)
        r = client.get("/api/assistant/conversations", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        conv_ids = [c["conversation_id"] for c in r.json()]
        assert cid in conv_ids


# ─────────────────────────────────────────────────────────────────────────────
# RATE LIMITING
# ─────────────────────────────────────────────────────────────────────────────

class TestRateLimit:
    def test_rate_limit_function_exists(self):
        from app.api.routes.assistant import _check_rate_limit
        # Should not raise with normal usage
        # (In-memory store, unique fake user ID)
        _check_rate_limit(999999)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminEndpoints:
    def test_admin_endpoint_requires_auth(self, client):
        r = client.get("/api/admin/users")
        assert r.status_code == 401

    def test_admin_endpoint_requires_admin_role(self, client, auth_headers):
        r = client.get("/api/admin/users", headers=auth_headers)
        assert r.status_code == 403

    def test_admin_promotes_self(self, client, auth_headers):
        """Test that we can promote a user to admin via DB and then access admin endpoint."""
        from app.core.database import SessionLocal
        from app.models.user import User

        # Get user ID
        r = client.get("/api/auth/me", headers=auth_headers)
        user_id = r.json()["id"]

        # Directly set role in DB (simulating an existing admin doing this)
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == user_id).first()
            u.role = "admin"
            db.commit()
        finally:
            db.close()

        # Now admin endpoint should work
        r2 = client.get("/api/admin/users", headers=auth_headers)
        assert r2.status_code == 200
        assert isinstance(r2.json(), list)
        assert len(r2.json()) > 0

        # Clean up
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == user_id).first()
            u.role = "user"
            db.commit()
        finally:
            db.close()

    def test_inactive_user_cannot_access_protected_endpoint(self, client, auth_headers):
        from app.core.database import SessionLocal
        from app.models.user import User

        user_id = client.get("/api/auth/me", headers=auth_headers).json()["id"]
        db = SessionLocal()
        try:
            db.query(User).filter(User.id == user_id).update({"is_active": False})
            db.commit()
        finally:
            db.close()

        response = client.get("/api/admin/users", headers=auth_headers)
        assert response.status_code == 401

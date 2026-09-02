"""
backend/app/api/routes/assistant.py

Milestone 4 — Conversational AI API endpoints.

POST /api/assistant/chat              — send a message, get AI response
GET  /api/assistant/history/{conv_id} — fetch conversation history
DELETE /api/assistant/history/{conv_id} — clear a conversation
GET  /api/assistant/conversations      — list all conversations for user
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import ConversationMessage, User

logger = logging.getLogger(__name__)
router = APIRouter()


# ── request / response schemas ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, description="Omit to start a new conversation")
    stream: bool = Field(default=False, description="Set true for streaming response")


class ChatResponse(BaseModel):
    response: str
    tools_used: list[str] = []
    conversation_id: str
    intent: str = "general"
    response_time_ms: float = 0.0


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    tools_used: list[str]
    timestamp: str
    response_time_ms: float | None


class ConversationOut(BaseModel):
    conversation_id: str
    message_count: int
    started_at: str
    last_message_at: str
    preview: str


# ── rate-limit helper ──────────────────────────────────────────────────────────

def _check_rate_limit(user_id: int) -> None:
    """
    Enforce per-user per-hour message limit.
    Uses Redis if available; falls back to in-memory dict.
    Raises HTTP 429 if exceeded.
    """
    from app.core.config import settings

    limit = settings.RATE_LIMIT_MESSAGES_PER_HOUR
    if limit <= 0:
        return  # disabled

    # Try Redis first
    if settings.REDIS_URL:
        try:
            import redis as redis_lib
            r = redis_lib.from_url(settings.REDIS_URL, decode_responses=True)
            key = f"rate:assistant:{user_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
            count = r.incr(key)
            if count == 1:
                r.expire(key, 3600)
            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded: {limit} messages per hour. Try again later.",
                )
            return
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("Redis rate-limit check failed, using in-memory: %s", exc)

    # In-memory fallback
    from collections import defaultdict
    import threading

    if not hasattr(_check_rate_limit, "_store"):
        _check_rate_limit._store = defaultdict(list)    # type: ignore[attr-defined]
        _check_rate_limit._lock  = threading.Lock()     # type: ignore[attr-defined]

    hour_key = f"{user_id}:{datetime.utcnow().strftime('%Y%m%d%H')}"
    cutoff = datetime.utcnow().timestamp() - 3600

    with _check_rate_limit._lock:                        # type: ignore[attr-defined]
        store = _check_rate_limit._store                 # type: ignore[attr-defined]
        # Prune old entries
        store[hour_key] = [t for t in store[hour_key] if t > cutoff]
        if len(store[hour_key]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {limit} messages per hour. Try again later.",
            )
        store[hour_key].append(datetime.utcnow().timestamp())


# ── helper: persist message to DB ──────────────────────────────────────────────

def _persist(
    db: Session,
    user_id: int,
    conversation_id: str,
    role: str,
    content: str,
    tools_used: list[str],
    response_time_ms: float | None = None,
) -> None:
    msg = ConversationMessage(
        user_id=user_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        tools_used=json.dumps(tools_used),
        response_time_ms=response_time_ms,
    )
    db.add(msg)
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the Digital Twin AI assistant",
)
def chat(
    body: ChatRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI assistant.

    - If **conversation_id** is omitted, a new UUID is generated automatically.
    - The assistant has access to 4 tools: savings forecast, simulation,
      full analytics, and personalised recommendations.
    - Set **stream=true** to receive a StreamingResponse of text tokens.
    """
    _check_rate_limit(current_user.id)

    # Generate or reuse conversation ID
    conv_id = body.conversation_id or str(uuid.uuid4())

    if body.stream:
        # Streaming path
        from app.services.conversational_ai import stream_chat

        def _generator():
            full = ""
            for token in stream_chat(current_user.id, body.message, conv_id):
                full += token
                yield token
            # Persist after streaming completes
            _persist(db, current_user.id, conv_id, "user", body.message, [])
            _persist(db, current_user.id, conv_id, "assistant", full, [])

        return StreamingResponse(_generator(), media_type="text/plain")

    # Non-streaming path
    from app.services.conversational_ai import chat as ai_chat

    try:
        result = ai_chat(current_user.id, body.message, conv_id)
    except Exception as exc:
        logger.error("chat endpoint error user=%s: %s", current_user.id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="AI service error. Please try again.")

    # Persist both turns
    _persist(db, current_user.id, conv_id, "user", body.message, [])
    _persist(
        db, current_user.id, conv_id, "assistant",
        result["response"],
        result.get("tools_used", []),
        result.get("response_time_ms"),
    )

    return ChatResponse(
        response=result["response"],
        tools_used=result.get("tools_used", []),
        conversation_id=conv_id,
        intent=result.get("intent", "general"),
        response_time_ms=result.get("response_time_ms", 0.0),
    )


@router.get(
    "/history/{conversation_id}",
    response_model=list[MessageOut],
    summary="Get full conversation history",
)
def get_history(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Return all messages in a conversation. Only the owner can access it."""
    messages = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.user_id == current_user.id,  # IDOR protection
        )
        .order_by(ConversationMessage.timestamp.asc())
        .all()
    )
    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            tools_used=json.loads(m.tools_used or "[]"),
            timestamp=m.timestamp.isoformat(),
            response_time_ms=m.response_time_ms,
        )
        for m in messages
    ]


@router.delete(
    "/history/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation and its history",
)
def delete_history(
    conversation_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Delete all messages in a conversation.
    Also clears the in-process memory window.
    Only the owner can delete their conversation.
    """
    # Verify ownership first
    exists = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.user_id == current_user.id,
        )
        .first()
    )
    if not exists:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    db.query(ConversationMessage).filter(
        ConversationMessage.conversation_id == conversation_id,
        ConversationMessage.user_id == current_user.id,
    ).delete()
    db.commit()

    # Clear in-process memory
    from app.services.conversational_ai import clear_memory
    clear_memory(conversation_id)


@router.get(
    "/conversations",
    response_model=list[ConversationOut],
    summary="List all conversations for the current user",
)
def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """Return a summary of every conversation the user has had."""
    rows = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.user_id == current_user.id)
        .order_by(ConversationMessage.timestamp.desc())
        .all()
    )

    # Group by conversation_id
    convs: dict[str, list[ConversationMessage]] = {}
    for msg in rows:
        convs.setdefault(msg.conversation_id, []).append(msg)

    result = []
    for conv_id, msgs in convs.items():
        # msgs are desc-ordered; reverse for chronological first
        msgs_asc = list(reversed(msgs))
        first_user = next((m for m in msgs_asc if m.role == "user"), msgs_asc[0])
        last_msg   = msgs_asc[-1]
        result.append(ConversationOut(
            conversation_id=conv_id,
            message_count=len(msgs_asc),
            started_at=msgs_asc[0].timestamp.isoformat(),
            last_message_at=last_msg.timestamp.isoformat(),
            preview=first_user.content[:80] + ("…" if len(first_user.content) > 80 else ""),
        ))

    result.sort(key=lambda x: x.last_message_at, reverse=True)
    return result

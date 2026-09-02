"""
backend/app/api/routes/admin.py

Milestone 4 — Admin-only endpoints.

Requires role='admin' on the authenticated user.
GET /api/admin/users          — list all users (no passwords exposed)
GET /api/admin/analytics-global — aggregate platform metrics
PATCH /api/admin/users/{user_id}/role — change a user's role
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


# ── admin dependency ───────────────────────────────────────────────────────────

def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Raise 403 if the authenticated user is not an admin."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


# ── schemas ────────────────────────────────────────────────────────────────────

class UserAdminOut(BaseModel):
    id: int
    name: str
    email: str
    age: int
    occupation: str
    is_active: bool
    role: str
    created_at: str


class RoleUpdate(BaseModel):
    role: str  # "user" | "admin"


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserAdminOut], summary="[Admin] List all users")
def list_users(
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    """Return all registered users. Passwords are never exposed."""
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        UserAdminOut(
            id=u.id, name=u.name, email=u.email, age=u.age,
            occupation=u.occupation, is_active=u.is_active,
            role=u.role, created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@router.patch(
    "/users/{user_id}/role",
    response_model=UserAdminOut,
    summary="[Admin] Change a user's role",
)
def update_role(
    user_id: int,
    body: RoleUpdate,
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    if body.role not in ("user", "admin"):
        raise HTTPException(status_code=422, detail="role must be 'user' or 'admin'.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.role = body.role
    db.commit()
    db.refresh(user)
    return UserAdminOut(
        id=user.id, name=user.name, email=user.email, age=user.age,
        occupation=user.occupation, is_active=user.is_active,
        role=user.role, created_at=user.created_at.isoformat(),
    )


@router.get("/analytics-global", summary="[Admin] Platform-wide aggregated metrics")
def global_analytics(
    admin: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    from app.models.user import (
        AnalyticsLog, ConversationMessage, FinancialRecord,
        FitnessActivity, Goal, Habit, SimulationResult, StudyActivity,
    )
    total_users         = db.query(User).count()
    active_users        = db.query(User).filter(User.is_active == True).count()
    total_fin_records   = db.query(FinancialRecord).count()
    total_study         = db.query(StudyActivity).count()
    total_habits        = db.query(Habit).count()
    total_fitness       = db.query(FitnessActivity).count()
    total_goals         = db.query(Goal).count()
    total_simulations   = db.query(SimulationResult).count()
    total_chat_messages = db.query(ConversationMessage).count()
    total_api_calls     = db.query(AnalyticsLog).count()
    from sqlalchemy import func
    avg_resp = db.query(func.avg(AnalyticsLog.response_time_ms)).scalar() or 0

    return {
        "users":           {"total": total_users, "active": active_users},
        "data_records":    {
            "financial": total_fin_records, "study": total_study,
            "habits": total_habits, "fitness": total_fitness, "goals": total_goals,
        },
        "platform_activity": {
            "simulations": total_simulations,
            "chat_messages": total_chat_messages,
            "api_calls": total_api_calls,
            "avg_response_ms": round(float(avg_resp), 2),
        },
    }

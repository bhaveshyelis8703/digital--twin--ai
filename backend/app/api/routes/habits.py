"""
backend/app/api/routes/habits.py
Milestone 1 CRUD + Milestone 2 analysis/productivity endpoints.

IMPORTANT: Named routes must be declared BEFORE /{habit_id}.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import Habit, User
from app.schemas.habit import HabitCreate, HabitResponse, HabitUpdate

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
#  MILESTONE 2 — ANALYSIS ENDPOINTS  (must come before /{habit_id})
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/analysis", summary="Full habit analysis: patterns, completion, risk flags")
def habit_analysis(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    try:
        from app.services.habit_service import get_habit_analysis
        habits_raw = [
            {"name": h.name, "completed": h.completed, "streak": h.streak}
            for h in db.query(Habit).filter(Habit.user_id == current_user.id).all()
        ]
        return get_habit_analysis(current_user.id, habits_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/productivity-index",
            summary="Productivity index with component breakdown (0-100)")
def productivity_index(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.habit_service import get_productivity_index
        return get_productivity_index(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trend", summary="4-week productivity forecast")
def productivity_trend(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.habit_service import get_productivity_trend
        return get_productivity_trend(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies", summary="Detect anomalous activity weeks")
def habit_anomalies(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.habit_service import get_anomalies
        return {"anomalies": get_anomalies(current_user.id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fitness-goal-probability",
            summary="Probability of reaching a fitness goal in N days")
def fitness_goal_probability(
    days_to_goal: int = 30,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    try:
        from app.services.habit_service import get_fitness_goal_probability
        return get_fitness_goal_probability(current_user.id, days_to_goal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
#  MILESTONE 1 — CRUD  (/{habit_id} must come AFTER named routes)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit(
    payload: HabitCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> HabitResponse:
    habit = Habit(user_id=current_user.id, **payload.model_dump())
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return HabitResponse.model_validate(habit)


@router.get("", response_model=list[HabitResponse])
def list_habits(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> list[HabitResponse]:
    habits = (
        db.query(Habit)
        .filter(Habit.user_id == current_user.id)
        .order_by(Habit.created_at.desc())
        .all()
    )
    return [HabitResponse.model_validate(h) for h in habits]


@router.get("/{habit_id}", response_model=HabitResponse)
def get_habit(
    habit_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> HabitResponse:
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return HabitResponse.model_validate(habit)


@router.put("/{habit_id}", response_model=HabitResponse)
def update_habit(
    habit_id: int,
    payload: HabitUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> HabitResponse:
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(habit, field, value)
    db.commit()
    db.refresh(habit)
    return HabitResponse.model_validate(habit)


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(
    habit_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> None:
    habit = db.query(Habit).filter(
        Habit.id == habit_id, Habit.user_id == current_user.id
    ).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()

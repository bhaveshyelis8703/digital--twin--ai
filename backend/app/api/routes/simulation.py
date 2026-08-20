"""
backend/app/api/routes/simulation.py

Simulation endpoints (Milestone 3).

POST /api/simulation/financial   – financial what-if simulations
POST /api/simulation/study       – study simulations
POST /api/simulation/habits      – habit simulations
POST /api/simulation/fitness     – fitness simulations
POST /api/simulation/goals       – goal completion probability
POST /api/simulation/full        – combined multi-domain simulation
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User

router = APIRouter()


# ── request bodies ────────────────────────────────────────────────────────────

class FinancialSimRequest(BaseModel):
    sim_type: str = Field(
        ...,
        description=(
            "savings_increase | major_purchase | expense_reduction | "
            "investment_growth | loan_impact"
        ),
    )
    monthly_increase: float       = Field(default=0,   ge=0)
    purchase_amount: float        = Field(default=0,   ge=0)
    purchase_month: int           = Field(default=3,   ge=1, le=60)
    reduction_pct: float          = Field(default=10,  ge=0, le=100)
    initial_amount: float         = Field(default=0,   ge=0)
    monthly_contribution: float   = Field(default=0,   ge=0)
    annual_return_pct: float      = Field(default=8.0, gt=0, le=50)
    loan_amount: float            = Field(default=0,   ge=0)
    annual_interest_pct: float    = Field(default=10.0, gt=0, le=100)
    tenure_months: int            = Field(default=24,  ge=1, le=360)
    horizon_months: int           = Field(default=12,  ge=1, le=60)


class StudySimRequest(BaseModel):
    sim_type: str = Field(
        ...,
        description="extra_hours | exam_prep | subject_improvement",
    )
    extra_hours_per_day: float  = Field(default=1.0, ge=0, le=8)
    subject: str                = Field(default="General")
    days_until_exam: int        = Field(default=30,   ge=1, le=365)
    target_score: float         = Field(default=80.0, ge=0, le=100)
    target_performance: float   = Field(default=80.0, ge=0, le=100)
    horizon_weeks: int          = Field(default=8,    ge=1, le=52)


class HabitSimRequest(BaseModel):
    sim_type: str = Field(
        ...,
        description="new_habit | remove_habit | productivity",
    )
    habit_name: str             = Field(default="New Habit")
    target_frequency: str       = Field(default="daily")
    focus_improvement_pct: float = Field(default=10.0, ge=-50, le=100)
    horizon_weeks: int          = Field(default=8,    ge=1, le=52)


class FitnessSimRequest(BaseModel):
    sim_type: str = Field(
        ...,
        description="workout_plan | weight_loss | goal_completion",
    )
    sessions_per_week: int           = Field(default=3,    ge=1, le=7)
    session_duration_minutes: float  = Field(default=45.0, gt=0, le=180)
    activity_type: str               = Field(default="Running")
    target_weekly_calories: float    = Field(default=1500, gt=0)
    goal_name: str                   = Field(default="Fitness Goal")
    horizon_weeks: int               = Field(default=8,    ge=1, le=52)


class GoalSimRequest(BaseModel):
    goal_id: int              = Field(..., gt=0)
    accelerate_by_pct: float  = Field(default=0.0, ge=0, le=200)


class FullSimRequest(BaseModel):
    horizon_months: int              = Field(default=6,    ge=1, le=36)
    financial_boost_pct: float       = Field(default=10.0, ge=0, le=100)
    study_hours_increase: float      = Field(default=1.0,  ge=0, le=8)
    habit_compliance_target: float   = Field(default=80.0, ge=0, le=100)
    fitness_sessions_per_week: int   = Field(default=3,    ge=0, le=7)


# ── helper ────────────────────────────────────────────────────────────────────

def _run(user_id: int, sim_type: str, params: dict):
    try:
        from app.services.digital_twin_service import run_simulation
        return run_simulation(user_id, sim_type, params)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/financial", summary="Run a financial what-if simulation")
def financial_simulation(
    body: FinancialSimRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    type_map = {
        "savings_increase":  "financial.savings_increase",
        "major_purchase":    "financial.major_purchase",
        "expense_reduction": "financial.expense_reduction",
        "investment_growth": "financial.investment_growth",
        "loan_impact":       "financial.loan_impact",
    }
    full_type = type_map.get(body.sim_type)
    if not full_type:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown sim_type '{body.sim_type}'. "
                   f"Valid: {list(type_map.keys())}",
        )
    return _run(current_user.id, full_type, body.model_dump())


@router.post("/study", summary="Run a study what-if simulation")
def study_simulation(
    body: StudySimRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    type_map = {
        "extra_hours":         "study.extra_hours",
        "exam_prep":           "study.exam_prep",
        "subject_improvement": "study.subject_improvement",
    }
    full_type = type_map.get(body.sim_type)
    if not full_type:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown sim_type '{body.sim_type}'. Valid: {list(type_map.keys())}",
        )
    return _run(current_user.id, full_type, body.model_dump())


@router.post("/habits", summary="Run a habit what-if simulation")
def habits_simulation(
    body: HabitSimRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    type_map = {
        "new_habit":    "habit.new_habit",
        "remove_habit": "habit.remove_habit",
        "productivity": "habit.productivity",
    }
    full_type = type_map.get(body.sim_type)
    if not full_type:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown sim_type '{body.sim_type}'. Valid: {list(type_map.keys())}",
        )
    return _run(current_user.id, full_type, body.model_dump())


@router.post("/fitness", summary="Run a fitness what-if simulation")
def fitness_simulation(
    body: FitnessSimRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    type_map = {
        "workout_plan":    "fitness.workout_plan",
        "weight_loss":     "fitness.weight_loss",
        "goal_completion": "fitness.goal_completion",
    }
    full_type = type_map.get(body.sim_type)
    if not full_type:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown sim_type '{body.sim_type}'. Valid: {list(type_map.keys())}",
        )
    return _run(current_user.id, full_type, body.model_dump())


@router.post("/goals", summary="Simulate goal completion probability")
def goals_simulation(
    body: GoalSimRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    return _run(current_user.id, "goal.completion_probability", body.model_dump())


@router.post("/full", summary="Combined multi-domain simulation")
def full_simulation(
    body: FullSimRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    return _run(current_user.id, "full", body.model_dump())


@router.get("/history", summary="Get simulation history for the current user")
def simulation_history(
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
):
    try:
        import json
        from app.core.database import SessionLocal
        from app.models.user import SimulationResult

        db = SessionLocal()
        try:
            rows = (
                db.query(SimulationResult)
                .filter(SimulationResult.user_id == current_user.id)
                .order_by(SimulationResult.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "scenario_name": r.scenario_name,
                    "scenario_type": r.scenario_type,
                    "confidence_score": r.confidence_score,
                    "created_at": r.created_at.isoformat(),
                    "input_data": json.loads(r.input_data),
                }
                for r in rows
            ]
        finally:
            db.close()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

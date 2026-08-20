"""
Pydantic V2 schemas for simulation request/response payloads (Milestone 3).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# SHARED SIMULATION RESPONSE
# ─────────────────────────────────────────────────────────────────────────────

class SimulationResult(BaseModel):
    simulation_type: str
    current_state: dict[str, Any]
    future_state: dict[str, Any]
    difference: dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    recommendations: list[str] = Field(default_factory=list)
    horizon_months: int = 12


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL SIMULATIONS
# ─────────────────────────────────────────────────────────────────────────────

class SavingsIncreaseRequest(BaseModel):
    monthly_increase: float = Field(..., gt=0, description="Extra monthly savings amount")
    horizon_months: int = Field(default=12, ge=1, le=60)


class MajorPurchaseRequest(BaseModel):
    purchase_amount: float = Field(..., gt=0)
    purchase_month: int = Field(default=3, ge=1, le=60)
    horizon_months: int = Field(default=12, ge=1, le=60)


class ExpenseReductionRequest(BaseModel):
    reduction_pct: float = Field(..., gt=0, le=100, description="% to reduce monthly expenses")
    horizon_months: int = Field(default=12, ge=1, le=60)


class InvestmentGrowthRequest(BaseModel):
    initial_amount: float = Field(..., gt=0)
    monthly_contribution: float = Field(default=0.0, ge=0)
    annual_return_pct: float = Field(default=8.0, gt=0, le=50)
    horizon_months: int = Field(default=24, ge=1, le=120)


class LoanImpactRequest(BaseModel):
    loan_amount: float = Field(..., gt=0)
    annual_interest_pct: float = Field(..., gt=0, le=100)
    tenure_months: int = Field(..., ge=1, le=360)


# ─────────────────────────────────────────────────────────────────────────────
# STUDY SIMULATIONS
# ─────────────────────────────────────────────────────────────────────────────

class ExtraStudyHoursRequest(BaseModel):
    extra_hours_per_day: float = Field(..., gt=0, le=8)
    horizon_weeks: int = Field(default=8, ge=1, le=52)


class ExamPreparationRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    days_until_exam: int = Field(..., ge=1, le=365)
    target_score: float = Field(..., ge=0, le=100)


class SubjectImprovementRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    target_performance: float = Field(..., ge=0, le=100)
    horizon_weeks: int = Field(default=8, ge=1, le=52)


# ─────────────────────────────────────────────────────────────────────────────
# HABIT SIMULATIONS
# ─────────────────────────────────────────────────────────────────────────────

class NewHabitRequest(BaseModel):
    habit_name: str = Field(..., min_length=1, max_length=100)
    target_frequency: str = Field(default="daily")
    horizon_weeks: int = Field(default=8, ge=1, le=52)


class HabitRemovalRequest(BaseModel):
    habit_name: str = Field(..., min_length=1)
    horizon_weeks: int = Field(default=4, ge=1, le=52)


class ProductivityChangeRequest(BaseModel):
    focus_improvement_pct: float = Field(..., ge=-50, le=100)
    horizon_weeks: int = Field(default=8, ge=1, le=52)


# ─────────────────────────────────────────────────────────────────────────────
# FITNESS SIMULATIONS
# ─────────────────────────────────────────────────────────────────────────────

class WorkoutPlanRequest(BaseModel):
    sessions_per_week: int = Field(..., ge=1, le=7)
    session_duration_minutes: float = Field(default=45.0, gt=0, le=180)
    activity_type: str = Field(default="Running")
    horizon_weeks: int = Field(default=8, ge=1, le=52)


class WeightLossRequest(BaseModel):
    target_weekly_calories: float = Field(..., gt=0, description="Weekly calorie burn target")
    horizon_weeks: int = Field(default=12, ge=1, le=52)


class FitnessGoalRequest(BaseModel):
    goal_name: str = Field(..., min_length=1)
    target_sessions: int = Field(..., ge=1)
    horizon_weeks: int = Field(default=8, ge=1, le=52)


# ─────────────────────────────────────────────────────────────────────────────
# GOAL SIMULATIONS
# ─────────────────────────────────────────────────────────────────────────────

class GoalCompletionRequest(BaseModel):
    goal_id: int = Field(..., gt=0)
    accelerate_by_pct: float = Field(default=0.0, ge=0, le=200)


# ─────────────────────────────────────────────────────────────────────────────
# FULL SIMULATION
# ─────────────────────────────────────────────────────────────────────────────

class FullSimulationRequest(BaseModel):
    horizon_months: int = Field(default=6, ge=1, le=36)
    financial_boost_pct: float = Field(default=10.0, ge=0, le=100)
    study_hours_increase: float = Field(default=1.0, ge=0, le=8)
    habit_compliance_target: float = Field(default=80.0, ge=0, le=100)
    fitness_sessions_per_week: int = Field(default=3, ge=0, le=7)

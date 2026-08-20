"""
Pydantic V2 schemas for the Digital Twin Simulation Engine (Milestone 3).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN STATE BLOCKS
# ─────────────────────────────────────────────────────────────────────────────

class FinancialState(BaseModel):
    total_income: float = 0.0
    total_expenses: float = 0.0
    net_savings: float = 0.0
    savings_rate: float = 0.0          # net_savings / total_income
    top_expense_category: str = ""
    monthly_avg_income: float = 0.0
    monthly_avg_expenses: float = 0.0
    record_count: int = 0


class StudyState(BaseModel):
    avg_study_hours: float = 0.0
    avg_focus_score: float = 0.0
    avg_performance_score: float = 0.0
    avg_task_completion: float = 0.0
    total_sessions: int = 0
    subjects: list[str] = Field(default_factory=list)
    study_streak_days: int = 0


class HabitState(BaseModel):
    total_habits: int = 0
    completed_habits: int = 0
    completion_rate: float = 0.0
    avg_streak: float = 0.0
    best_streak: int = 0
    at_risk_habits: list[str] = Field(default_factory=list)


class FitnessState(BaseModel):
    total_sessions: int = 0
    avg_duration: float = 0.0
    avg_calories: float = 0.0
    total_calories: float = 0.0
    activity_types: list[str] = Field(default_factory=list)
    sessions_per_week: float = 0.0


class GoalSummary(BaseModel):
    id: int
    name: str
    status: str
    progress_pct: float
    days_remaining: int
    on_track: bool


class BehavioralPatterns(BaseModel):
    consistency_score: float = 0.0     # 0-100
    discipline_score: float = 0.0
    growth_trajectory: str = "stable"  # improving | stable | declining
    strongest_domain: str = ""
    weakest_domain: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# UNIFIED TWIN STATE
# ─────────────────────────────────────────────────────────────────────────────

class TwinState(BaseModel):
    user_id: int
    snapshot_at: datetime
    financial: FinancialState = Field(default_factory=FinancialState)
    study: StudyState = Field(default_factory=StudyState)
    habits: HabitState = Field(default_factory=HabitState)
    fitness: FitnessState = Field(default_factory=FitnessState)
    goals: list[GoalSummary] = Field(default_factory=list)
    productivity_score: float = 0.0
    risk_score: float = 0.0
    behavioral_patterns: BehavioralPatterns = Field(default_factory=BehavioralPatterns)

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────────────────────────────────────────
# SNAPSHOT DB MODEL
# ─────────────────────────────────────────────────────────────────────────────

class SnapshotResponse(BaseModel):
    id: int
    user_id: int
    scenario_name: str
    scenario_type: str
    input_data: dict[str, Any]
    result_data: dict[str, Any]
    confidence_score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CreateSnapshotRequest(BaseModel):
    scenario_name: str = Field(default="baseline", min_length=1, max_length=100)


# ─────────────────────────────────────────────────────────────────────────────
# PROJECTION
# ─────────────────────────────────────────────────────────────────────────────

class ProjectionRequest(BaseModel):
    horizon_months: int = Field(default=6, ge=1, le=36)
    include_domains: list[str] = Field(
        default_factory=lambda: ["financial", "study", "habits", "fitness", "goals"]
    )


class DomainProjection(BaseModel):
    domain: str
    current_value: float
    projected_value: float
    change_pct: float
    confidence: float
    key_drivers: list[str] = Field(default_factory=list)


class ProjectionResponse(BaseModel):
    user_id: int
    horizon_months: int
    projections: list[DomainProjection]
    overall_trajectory: str
    risk_flags: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────

class Recommendation(BaseModel):
    domain: str
    priority: str          # high | medium | low
    impact: str            # high | medium | low
    confidence: float      # 0.0–1.0
    title: str
    description: str
    action_steps: list[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    user_id: int
    generated_at: datetime
    recommendations: list[Recommendation]
    overall_health_score: float


# ─────────────────────────────────────────────────────────────────────────────
# TWIN SUMMARY (lightweight)
# ─────────────────────────────────────────────────────────────────────────────

class TwinSummaryResponse(BaseModel):
    user_id: int
    overall_score: float
    financial_score: float
    study_score: float
    habits_score: float
    fitness_score: float
    goals_score: float
    risk_level: str        # low | medium | high
    top_insight: str
    generated_at: datetime

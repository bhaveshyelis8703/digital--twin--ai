"""
Pydantic V2 schemas for scenario comparison (Milestone 3).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ScenarioDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    parameters: dict[str, Any] = Field(default_factory=dict)


class ScenarioCompareRequest(BaseModel):
    scenario_a: ScenarioDefinition
    scenario_b: ScenarioDefinition
    horizon_months: int = Field(default=12, ge=1, le=60)
    domains: list[str] = Field(
        default_factory=lambda: ["financial", "study", "habits", "fitness"]
    )


class DomainImpact(BaseModel):
    domain: str
    scenario_a_score: float
    scenario_b_score: float
    winner: str       # "A" | "B" | "tie"
    delta: float
    rationale: str


class ScenarioCompareResponse(BaseModel):
    scenario_a_name: str
    scenario_b_name: str
    overall_winner: str   # "A" | "B" | "tie"
    domain_impacts: list[DomainImpact]
    scenario_a_risk: float
    scenario_b_risk: float
    recommendation: str
    confidence: float


class BestPathResponse(BaseModel):
    user_id: int
    recommended_path: str
    path_description: str
    expected_score_gain: float
    horizon_months: int
    milestones: list[dict[str, Any]] = Field(default_factory=list)
    top_actions: list[str] = Field(default_factory=list)


class RiskAnalysisRequest(BaseModel):
    scenario: ScenarioDefinition
    horizon_months: int = Field(default=12, ge=1, le=60)


class RiskFactor(BaseModel):
    domain: str
    risk_type: str
    severity: str     # low | medium | high | critical
    probability: float
    description: str
    mitigation: str


class RiskAnalysisResponse(BaseModel):
    overall_risk_score: float   # 0–100
    risk_level: str             # low | medium | high | critical
    risk_factors: list[RiskFactor]
    safe_to_proceed: bool
    summary: str

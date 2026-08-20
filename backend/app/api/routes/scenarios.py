"""
backend/app/api/routes/scenarios.py

Scenario comparison endpoints (Milestone 3).

POST /api/scenarios/compare       – head-to-head A vs B
GET  /api/scenarios/best-path     – best recommended path for user
POST /api/scenarios/risk-analysis – risk breakdown for a scenario
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.routes.auth import get_current_user
from app.models.user import User

router = APIRouter()


# ── request models ────────────────────────────────────────────────────────────

class ScenarioDef(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    sim_type: str = Field(..., description="Simulation type key, e.g. financial.savings_increase")
    parameters: dict[str, Any] = Field(default_factory=dict)


class CompareRequest(BaseModel):
    scenario_a: ScenarioDef
    scenario_b: ScenarioDef
    horizon_months: int = Field(default=12, ge=1, le=60)
    domains: list[str] = Field(
        default_factory=lambda: ["financial", "study", "habits", "fitness"]
    )


class RiskRequest(BaseModel):
    scenario: ScenarioDef
    horizon_months: int = Field(default=12, ge=1, le=60)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/compare", summary="Compare two scenarios head-to-head")
def compare_scenarios(
    body: CompareRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.scenario_service import compare_two_scenarios
        return compare_two_scenarios(
            current_user.id,
            body.scenario_a.model_dump(),
            body.scenario_b.model_dump(),
            body.horizon_months,
            body.domains,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/best-path", summary="Identify the single best improvement path for the user")
def best_path(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.scenario_service import best_future_path
        return best_future_path(current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/risk-analysis", summary="Full risk breakdown for a given scenario")
def risk_analysis(
    body: RiskRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.scenario_service import risk_comparison
        return risk_comparison(
            current_user.id,
            body.scenario.model_dump(),
            body.horizon_months,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/rank", summary="Rank a list of scenarios by projected impact")
def rank_scenarios(
    scenarios: list[ScenarioDef],
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.scenario_service import rank_scenarios as _rank
        return _rank(current_user.id, [s.model_dump() for s in scenarios])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/impact", summary="Domain-level impact analysis between two scenarios")
def impact_analysis(
    body: CompareRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.scenario_service import impact_analysis as _impact
        return _impact(
            current_user.id,
            body.scenario_a.model_dump(),
            body.scenario_b.model_dump(),
            body.domains,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

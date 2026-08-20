"""
backend/app/api/routes/digital_twin.py

Digital Twin endpoints (Milestone 3).

GET  /api/digital-twin/snapshot       – latest persisted snapshot
GET  /api/digital-twin/summary        – lightweight scores + risk level
POST /api/digital-twin/create-snapshot – save current state
POST /api/digital-twin/project        – forward projection
POST /api/digital-twin/compare        – compare two state dicts
POST /api/digital-twin/recommendations – AI recommendations
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import SimulationResult, User

router = APIRouter()


# ── inline request models ─────────────────────────────────────────────────────

class CreateSnapshotBody(BaseModel):
    scenario_name: str = Field(default="baseline", min_length=1, max_length=100)


class ProjectBody(BaseModel):
    horizon_months: int = Field(default=6, ge=1, le=36)
    include_domains: list[str] = Field(
        default_factory=lambda: ["financial", "study", "habits", "fitness", "goals"]
    )


class CompareBody(BaseModel):
    state_a: dict[str, Any]
    state_b: dict[str, Any]
    label_a: str = Field(default="State A")
    label_b: str = Field(default="State B")


# ── lazy service import ───────────────────────────────────────────────────────

def _svc():
    from app.services.digital_twin_service import (
        create_snapshot,
        generate_ai_insights,
        generate_recommendations,
        generate_risk_analysis,
        get_current_twin,
    )
    return get_current_twin, create_snapshot, generate_ai_insights, generate_risk_analysis, generate_recommendations


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/snapshot", summary="Get latest persisted snapshot for the current user")
def get_snapshot(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    row = (
        db.query(SimulationResult)
        .filter(
            SimulationResult.user_id == current_user.id,
            SimulationResult.scenario_type == "snapshot",
        )
        .order_by(SimulationResult.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No snapshot found. Create one first.")
    import json
    return {
        "id": row.id,
        "user_id": row.user_id,
        "scenario_name": row.scenario_name,
        "confidence_score": row.confidence_score,
        "created_at": row.created_at.isoformat(),
        "result_data": json.loads(row.result_data),
    }


@router.get("/summary", summary="Lightweight Digital Twin summary with domain scores")
def get_summary(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.ml.digital_twin import DigitalTwin
        twin = DigitalTwin(current_user.id).load_from_database()
        return twin.generate_summary()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/create-snapshot", summary="Persist current twin state as a named snapshot")
def create_snapshot_endpoint(
    body: CreateSnapshotBody,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        _, snap_fn, *_ = _svc()
        return snap_fn(current_user.id, body.scenario_name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/project", summary="Project the Digital Twin state N months into the future")
def project_state(
    body: ProjectBody,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.ml.digital_twin import DigitalTwin
        twin = DigitalTwin(current_user.id).load_from_database()
        projection = twin.project_state(body.horizon_months)
        # filter to requested domains
        if body.include_domains:
            projection = {
                k: v for k, v in projection.items()
                if k not in ("financial", "study", "habits", "fitness", "goals")
                or k in body.include_domains
            }
        return projection
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/compare", summary="Compare two state snapshots and return a delta report")
def compare_states(
    body: CompareBody,
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.ml.digital_twin import DigitalTwin
        return DigitalTwin.compare_states(
            body.state_a, body.state_b, body.label_a, body.label_b
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recommendations", summary="Generate AI recommendations for the current user")
def get_recommendations(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        *_, rec_fn = _svc()
        return rec_fn(current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/risk", summary="Current risk analysis across all domains")
def get_risk(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.digital_twin_service import generate_risk_analysis
        return generate_risk_analysis(current_user.id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

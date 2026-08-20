"""
backend/app/api/routes/analytics.py
Milestone 1 activity log + Milestone 2 full-report endpoint.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.user import AnalyticsLog, User
from app.schemas.analytics import AnalyticsLogResponse

router = APIRouter()


# ── Milestone 1 ───────────────────────────────────────────────────────────────

@router.get("/activity-log", response_model=list[AnalyticsLogResponse])
def get_activity_log(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> list[AnalyticsLogResponse]:
    logs = (
        db.query(AnalyticsLog)
        .filter(AnalyticsLog.user_id == current_user.id)
        .order_by(AnalyticsLog.timestamp.desc())
        .all()
    )
    return [AnalyticsLogResponse.model_validate(item) for item in logs]


# ── Milestone 2 ───────────────────────────────────────────────────────────────

@router.get("/full-report",
            summary="Complete analytics report: financial + study + habits (ML-powered)")
@router.get("/full",
            summary="Alias for /full-report")
async def full_analytics_report(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Aggregates all ML predictions for the current user.
    Runs independent sub-services concurrently.
    Response time target: < 3 seconds.
    """
    try:
        from app.services.analytics_service import get_full_analytics
        return await get_full_analytics(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {e}")


@router.get("/summary", summary="Quick analytics summary (alias)")
async def analytics_summary(
    current_user: Annotated[User, Depends(get_current_user)],
):
    try:
        from app.services.analytics_service import get_full_analytics
        data = await get_full_analytics(current_user.id)
        return {
            "total_requests":     data.get("api_usage", {}).get("total_requests", 0),
            "avg_response_ms":    data.get("api_usage", {}).get("avg_response_ms", 0),
            "productivity_index": data.get("habits", {}).get("productivity_index", 0),
            "study_readiness":    data.get("study", {}).get("exam_readiness", {}).get("score", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs", response_model=list[AnalyticsLogResponse],
            summary="Alias for /activity-log")
def get_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
) -> list[AnalyticsLogResponse]:
    logs = (
        db.query(AnalyticsLog)
        .filter(AnalyticsLog.user_id == current_user.id)
        .order_by(AnalyticsLog.timestamp.desc())
        .limit(100)
        .all()
    )
    return [AnalyticsLogResponse.model_validate(item) for item in logs]

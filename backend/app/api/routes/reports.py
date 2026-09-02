"""
backend/app/api/routes/reports.py

Milestone 4 — PDF Report endpoints.

GET /api/reports/generate?type=full          — Download full PDF report
GET /api/reports/generate?type=financial     — Financial section only
GET /api/reports/generate?type=goals         — Goals section only
GET /api/reports/generate?type=study         — Study section only
GET /api/reports/generate?type=recommendations — Recommendations only
GET /api/reports/comparison?period_a=1M&period_b=1Y — Period comparison JSON
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.routes.auth import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

_VALID_TYPES = ("full", "financial", "goals", "study", "recommendations")


@router.get("/generate", summary="Generate and download a PDF report")
def generate_report(
    type: str = Query(default="full", description=f"Report type: {_VALID_TYPES}"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """
    Generate a personalised PDF report for the authenticated user.
    Returns the PDF as a binary download (application/pdf).
    """
    if type not in _VALID_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid report type '{type}'. Valid: {list(_VALID_TYPES)}",
        )

    try:
        from app.services.report_service import generate_pdf_report
        pdf_bytes = generate_pdf_report(current_user.id, report_type=type)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error("PDF generation error user=%s: %s", current_user.id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Report generation failed. Please try again.")

    filename = f"digital_twin_{type}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/comparison", summary="Period-over-period comparison data")
def period_comparison(
    period_a: str = Query(default="1M", description="Earlier period: 1M | 3M | 6M | 1Y"),
    period_b: str = Query(default="1Y", description="Later period: 1M | 3M | 6M | 1Y"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """
    Compare two time periods for the authenticated user.
    Returns aggregated metrics for both periods and the delta.
    """
    from datetime import timedelta
    from app.core.database import SessionLocal
    from app.models.user import FinancialRecord, FitnessActivity, Goal, Habit, StudyActivity
    from sqlalchemy import func

    _PERIOD_DAYS = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365}

    valid = list(_PERIOD_DAYS.keys())
    if period_a not in valid or period_b not in valid:
        raise HTTPException(status_code=422, detail=f"Periods must be one of {valid}")

    now = datetime.utcnow()
    # Compare adjacent windows of the same length. This prevents the selected
    # periods from overlapping or comparing unlike durations.
    window_days = min(_PERIOD_DAYS[period_a], _PERIOD_DAYS[period_b])
    cutoff_b_end   = now
    cutoff_b_start = now - timedelta(days=window_days)
    cutoff_a_end   = cutoff_b_start
    cutoff_a_start = cutoff_a_end - timedelta(days=window_days)

    db = SessionLocal()
    uid = current_user.id

    def _fin(start, end):
        recs = db.query(FinancialRecord).filter(
            FinancialRecord.user_id == uid,
            FinancialRecord.date >= start,
            FinancialRecord.date <= end,
        ).all()
        inc  = sum(r.amount for r in recs if r.record_type == "income")
        exp  = sum(r.amount for r in recs if r.record_type == "expense")
        return {"income": round(inc, 2), "expenses": round(exp, 2), "net": round(inc - exp, 2)}

    def _study(start, end):
        rows = db.query(StudyActivity).filter(
            StudyActivity.user_id == uid,
            StudyActivity.study_date >= start,
            StudyActivity.study_date <= end,
        ).all()
        n = len(rows)
        return {
            "sessions": n,
            "avg_hours": round(sum(r.study_hours for r in rows) / n, 2) if n else 0,
            "avg_performance": round(sum(r.performance_score for r in rows) / n, 1) if n else 0,
        }

    def _fitness(start, end):
        rows = db.query(FitnessActivity).filter(
            FitnessActivity.user_id == uid,
            FitnessActivity.activity_date >= start,
            FitnessActivity.activity_date <= end,
        ).all()
        n = len(rows)
        return {
            "sessions": n,
            "avg_calories": round(sum(r.calories_burned for r in rows) / n, 1) if n else 0,
            "total_calories": round(sum(r.calories_burned for r in rows), 1),
        }

    def _habits(start, end):
        rows = db.query(Habit).filter(
            Habit.user_id == uid,
            Habit.created_at >= start,
            Habit.created_at <= end,
        ).all()
        n = len(rows)
        completed = sum(1 for r in rows if r.completed)
        return {
            "total": n,
            "completed": completed,
            "completion_rate": round(completed / n * 100, 1) if n else 0,
        }

    try:
        a_fin   = _fin(cutoff_a_start, cutoff_a_end)
        b_fin   = _fin(cutoff_b_start, cutoff_b_end)
        a_study = _study(cutoff_a_start, cutoff_a_end)
        b_study = _study(cutoff_b_start, cutoff_b_end)
        a_fit   = _fitness(cutoff_a_start, cutoff_a_end)
        b_fit   = _fitness(cutoff_b_start, cutoff_b_end)
        a_hab   = _habits(cutoff_a_start, cutoff_a_end)
        b_hab   = _habits(cutoff_b_start, cutoff_b_end)
    finally:
        db.close()

    def _delta(a_val, b_val, higher_is_better=True):
        if isinstance(a_val, (int, float)) and isinstance(b_val, (int, float)):
            change = b_val - a_val
            pct    = (change / abs(a_val) * 100) if a_val != 0 else 0
            improved = change > 0 if higher_is_better else change < 0
            return {"change": round(change, 2), "pct": round(pct, 1), "improved": improved}
        return {}

    return {
        "period_a": {"label": period_a, "start": cutoff_a_start.date().isoformat(), "end": cutoff_a_end.date().isoformat()},
        "period_b": {"label": period_b, "start": cutoff_b_start.date().isoformat(), "end": cutoff_b_end.date().isoformat()},
        "financial": {
            "period_a": a_fin, "period_b": b_fin,
            "delta": {
                "income":   _delta(a_fin["income"],   b_fin["income"]),
                "expenses": _delta(a_fin["expenses"], b_fin["expenses"], higher_is_better=False),
                "net":      _delta(a_fin["net"],      b_fin["net"]),
            },
        },
        "study": {
            "period_a": a_study, "period_b": b_study,
            "delta": {
                "sessions":        _delta(a_study["sessions"],        b_study["sessions"]),
                "avg_hours":       _delta(a_study["avg_hours"],       b_study["avg_hours"]),
                "avg_performance": _delta(a_study["avg_performance"], b_study["avg_performance"]),
            },
        },
        "fitness": {
            "period_a": a_fit, "period_b": b_fit,
            "delta": {
                "sessions":       _delta(a_fit["sessions"],       b_fit["sessions"]),
                "avg_calories":   _delta(a_fit["avg_calories"],   b_fit["avg_calories"]),
                "total_calories": _delta(a_fit["total_calories"], b_fit["total_calories"]),
            },
        },
        "habits": {
            "period_a": a_hab, "period_b": b_hab,
            "delta": {
                "completion_rate": _delta(a_hab["completion_rate"], b_hab["completion_rate"]),
            },
        },
    }

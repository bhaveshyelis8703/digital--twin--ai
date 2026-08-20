"""
backend/app/services/analytics_service.py
Unified full-report aggregator — calls all sub-services concurrently.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_ML   = _ROOT / "ml"
for _p in [str(_ROOT), str(_ML)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _safe(fn, *args, **kwargs):
    """Call fn, return result or error dict on exception."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return {"error": str(e)}


async def get_full_analytics(user_id: int) -> dict:
    """
    Aggregate all ML predictions for one user.
    Independent calls run concurrently via asyncio.gather.
    """
    from app.services.forecasting_service import (
        generate_savings_projection,
        generate_cashflow_forecast,
    )
    from app.services.study_service import (
        get_exam_readiness,
        get_study_trend,
    )
    from app.services.habit_service import (
        get_productivity_index,
        get_productivity_trend,
        get_anomalies,
    )
    from ml.data_preparation import (
        load_financial_data, load_study_data, load_fitness_data,
    )
    from ml.habit_analysis import habit_consistency_score
    from app.core.database import SessionLocal
    from app.models.user import Habit

    loop = asyncio.get_event_loop()

    # Run all blocking ML calls in the thread-pool concurrently
    (
        savings_proj,
        cashflow,
        exam_readiness,
        study_trend_r,
        productivity,
        prod_trend,
        anomalies,
    ) = await asyncio.gather(
        loop.run_in_executor(None, lambda: _safe(generate_savings_projection, user_id, 6)),
        loop.run_in_executor(None, lambda: _safe(generate_cashflow_forecast,   user_id, 6)),
        loop.run_in_executor(None, lambda: _safe(get_exam_readiness,           user_id)),
        loop.run_in_executor(None, lambda: _safe(get_study_trend,              user_id)),
        loop.run_in_executor(None, lambda: _safe(get_productivity_index,       user_id)),
        loop.run_in_executor(None, lambda: _safe(get_productivity_trend,       user_id)),
        loop.run_in_executor(None, lambda: _safe(get_anomalies,                user_id)),
    )

    # Habit consistency (needs habits_raw — quick DB call)
    db = SessionLocal()
    try:
        habits_raw = [
            {"name": h.name, "completed": h.completed, "streak": h.streak}
            for h in db.query(Habit).filter(Habit.user_id == user_id).all()
        ]
    finally:
        db.close()
    consistency = _safe(habit_consistency_score, habits_raw)

    # Financial summary
    fin_df = load_financial_data(user_id)
    fin_summary = {}
    if not fin_df.empty:
        income   = float(fin_df[fin_df["record_type"] == "income"]["amount"].sum())
        expenses = float(fin_df[fin_df["record_type"] == "expense"]["amount"].sum())
        fin_summary = {
            "total_income":   round(income, 2),
            "total_expenses": round(expenses, 2),
            "net_savings":    round(income - expenses, 2),
            "record_count":   len(fin_df),
        }

    # Study summary
    study_df   = load_study_data(user_id)
    study_summary = {}
    if not study_df.empty:
        study_summary = {
            "total_sessions":    len(study_df),
            "total_hours":       round(float(study_df["study_hours"].sum()), 1),
            "avg_performance":   round(float(study_df["performance_score"].mean()), 1),
            "avg_focus":         round(float(study_df["focus_score"].mean()), 1),
        }

    return {
        "user_id": user_id,
        "financial": {
            "summary":           fin_summary,
            "savings_projection": savings_proj,
            "cashflow_forecast":  cashflow,
        },
        "study": {
            "summary":      study_summary,
            "exam_readiness": exam_readiness,
            "trend":          study_trend_r,
        },
        "habits": {
            "consistency":      consistency,
            "productivity_index": productivity,
            "productivity_trend": prod_trend,
            "anomalies":         anomalies,
        },
    }

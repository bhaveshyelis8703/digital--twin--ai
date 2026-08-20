"""
backend/app/services/digital_twin_service.py

Service layer that wraps DigitalTwin + SimulationEngine and is called
exclusively by the API route handlers.  Never imports FastAPI constructs
(no Request, Depends, etc.) so it can also be used in background tasks.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parents[2]
_ROOT    = _BACKEND.parent
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── lazy factory helpers ──────────────────────────────────────────────────────

def _twin(user_id: int):
    from app.ml.digital_twin import DigitalTwin
    return DigitalTwin(user_id).load_from_database()


def _engine(user_id: int):
    from app.ml.simulation_engine import SimulationEngine
    return SimulationEngine(user_id)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC SERVICE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_current_twin(user_id: int) -> dict[str, Any]:
    """Build and return the full current twin state."""
    return _twin(user_id).build_current_state()


def create_snapshot(user_id: int, scenario_name: str = "baseline") -> dict[str, Any]:
    """Persist a named snapshot of the current state and return the saved record."""
    return _twin(user_id).save_snapshot(scenario_name)


def run_simulation(
    user_id: int,
    sim_type: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """
    Dispatch a single domain simulation by type string.

    sim_type values
    ---------------
    financial.savings_increase | financial.major_purchase |
    financial.expense_reduction | financial.investment_growth |
    financial.loan_impact |
    study.extra_hours | study.exam_prep | study.subject_improvement |
    habit.new_habit | habit.remove_habit | habit.productivity |
    fitness.workout_plan | fitness.weight_loss | fitness.goal_completion |
    goal.completion_probability | full
    """
    eng = _engine(user_id)

    dispatch: dict[str, Any] = {
        "financial.savings_increase":   (eng.simulate_savings_increase,
                                         ["monthly_increase", "horizon_months"]),
        "financial.major_purchase":     (eng.simulate_major_purchase,
                                         ["purchase_amount", "purchase_month", "horizon_months"]),
        "financial.expense_reduction":  (eng.simulate_expense_reduction,
                                         ["reduction_pct", "horizon_months"]),
        "financial.investment_growth":  (eng.simulate_investment_growth,
                                         ["initial_amount", "monthly_contribution",
                                          "annual_return_pct", "horizon_months"]),
        "financial.loan_impact":        (eng.simulate_loan_impact,
                                         ["loan_amount", "annual_interest_pct", "tenure_months"]),
        "study.extra_hours":            (eng.simulate_extra_study_hours,
                                         ["extra_hours_per_day", "horizon_weeks"]),
        "study.exam_prep":              (eng.simulate_exam_preparation,
                                         ["subject", "days_until_exam", "target_score"]),
        "study.subject_improvement":    (eng.simulate_subject_improvement,
                                         ["subject", "target_performance", "horizon_weeks"]),
        "habit.new_habit":              (eng.simulate_new_habit,
                                         ["habit_name", "target_frequency", "horizon_weeks"]),
        "habit.remove_habit":           (eng.simulate_habit_removal,
                                         ["habit_name", "horizon_weeks"]),
        "habit.productivity":           (eng.simulate_productivity_change,
                                         ["focus_improvement_pct", "horizon_weeks"]),
        "fitness.workout_plan":         (eng.simulate_workout_plan,
                                         ["sessions_per_week", "session_duration_minutes",
                                          "activity_type", "horizon_weeks"]),
        "fitness.weight_loss":          (eng.simulate_weight_loss,
                                         ["target_weekly_calories", "horizon_weeks"]),
        "fitness.goal_completion":      (eng.simulate_goal_completion,
                                         ["goal_name", "horizon_weeks"]),
        "goal.completion_probability":  (eng.simulate_goal_completion_probability,
                                         ["goal_id", "accelerate_by_pct"]),
        "full":                         (eng.simulate_full,
                                         ["horizon_months", "financial_boost_pct",
                                          "study_hours_increase",
                                          "habit_compliance_target",
                                          "fitness_sessions_per_week"]),
    }

    if sim_type not in dispatch:
        return {"error": f"Unknown simulation type: {sim_type}",
                "valid_types": list(dispatch.keys())}

    fn, arg_names = dispatch[sim_type]
    kwargs = {k: params[k] for k in arg_names if k in params}

    result = fn(**kwargs)

    # ── persist result ────────────────────────────────────────────────
    _persist_simulation(user_id, sim_type, params, result)

    return result


def compare_scenarios(
    user_id: int,
    scenario_a: dict[str, Any],
    scenario_b: dict[str, Any],
    horizon_months: int = 12,
) -> dict[str, Any]:
    """Run two simulations and compare them head-to-head."""
    from app.services.scenario_service import compare_two_scenarios
    return compare_two_scenarios(user_id, scenario_a, scenario_b, horizon_months)


def generate_ai_insights(user_id: int) -> dict[str, Any]:
    """Return AI-derived insights from recommendation_service."""
    from app.services.recommendation_service import generate_all_recommendations
    return generate_all_recommendations(user_id)


def generate_risk_analysis(user_id: int) -> dict[str, Any]:
    """Compute current risk exposure across all domains."""
    tw   = _twin(user_id)
    risk = tw.calculate_risk_score()
    fin  = tw._financial_state()
    hab  = tw._habits_state()
    fit  = tw._fitness_state()
    gls  = tw._goals_state()
    stu  = tw._study_state()

    risk_level = "low" if risk < 30 else "medium" if risk < 60 else "high"

    factors: list[dict[str, Any]] = []

    if fin["net_savings"] < 0:
        factors.append({"domain": "financial", "severity": "high",
                        "description": "Negative net savings – spending exceeds income.",
                        "mitigation": "Reduce discretionary expenses by 10–15% immediately."})
    elif fin["savings_rate"] < 0.05:
        factors.append({"domain": "financial", "severity": "medium",
                        "description": "Savings rate below 5%.",
                        "mitigation": "Target 10% savings rate as a baseline."})

    if hab["completion_rate"] < 0.4:
        factors.append({"domain": "habits", "severity": "high",
                        "description": f"Only {hab['completion_rate']*100:.0f}% of habits completed.",
                        "mitigation": "Reduce habit count and focus on 2–3 core habits."})

    if fit["sessions_per_week"] < 1:
        factors.append({"domain": "fitness", "severity": "medium",
                        "description": "Less than one fitness session per week.",
                        "mitigation": "Commit to one 30-min session per week to start."})

    overdue = sum(1 for g in gls if not g["on_track"] and g["days_remaining"] < 30)
    if overdue > 0:
        factors.append({"domain": "goals", "severity": "medium",
                        "description": f"{overdue} goal(s) overdue within 30 days.",
                        "mitigation": "Update goal timelines or increase weekly effort."})

    if stu["avg_performance_score"] < 50 and stu["total_sessions"] > 0:
        factors.append({"domain": "study", "severity": "medium",
                        "description": f"Average performance score below 50 ({stu['avg_performance_score']:.0f}).",
                        "mitigation": "Review study technique – active recall over passive re-reading."})

    return {
        "user_id":          user_id,
        "overall_risk_score": risk,
        "risk_level":        risk_level,
        "risk_factors":      factors,
        "safe_to_proceed":   risk < 60,
        "analysed_at":       datetime.utcnow().isoformat(),
    }


def generate_recommendations(user_id: int) -> dict[str, Any]:
    """Wrapper delegating to recommendation_service."""
    from app.services.recommendation_service import generate_all_recommendations
    return generate_all_recommendations(user_id)


# ── private helpers ───────────────────────────────────────────────────────────

def _persist_simulation(
    user_id: int,
    sim_type: str,
    params: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """Save simulation run to DB (fire-and-forget; errors are swallowed)."""
    try:
        from app.core.database import SessionLocal
        from app.models.user import SimulationResult

        db = SessionLocal()
        try:
            row = SimulationResult(
                user_id=user_id,
                scenario_name=params.get("scenario_name", sim_type),
                scenario_type=sim_type,
                input_data=json.dumps(params),
                result_data=json.dumps(result),
                confidence_score=float(result.get("confidence_score", 0)),
            )
            db.add(row)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass  # non-critical – simulation result still returned to caller

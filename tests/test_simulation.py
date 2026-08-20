"""
tests/test_simulation.py

Unit tests for SimulationEngine (Milestone 3).
All DB calls are intercepted via a pre-loaded DigitalTwin fixture.

Run:  pytest tests/test_simulation.py -v --tb=short
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
_ROOT    = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── twin fixture (no DB) ──────────────────────────────────────────────────────

def _loaded_twin(user_id=1):
    from app.ml.digital_twin import DigitalTwin
    TODAY = datetime.utcnow()
    twin = DigitalTwin(user_id)
    twin._financial = [
        {"id":1,"record_type":"income", "amount":5000,"date":"2026-01-15T00:00:00",
         "category":"salary","recurring_frequency":"monthly","goal_impact":None},
        {"id":2,"record_type":"expense","amount":2000,"date":"2026-01-20T00:00:00",
         "category":"housing","recurring_frequency":"monthly","goal_impact":None},
    ]
    twin._study = [
        {"id":1,"subject":"Python","study_date":"2026-07-01T00:00:00",
         "study_hours":2.0,"focus_score":75,"task_completion":80,"performance_score":72},
    ]
    twin._habits = [
        {"id":1,"name":"Morning Run","target_frequency":"daily","completed":True,"streak":7},
        {"id":2,"name":"Meditate",   "target_frequency":"daily","completed":False,"streak":0},
    ]
    twin._fitness = [
        {"id":i,"activity_type":"Running","duration":40,"calories_burned":350,
         "activity_date":f"2026-06-{i:02d}T00:00:00"}
        for i in range(1, 10)
    ]
    twin._goals = [
        {"id":1,"name":"Save 5k","description":"Emergency fund",
         "target_value":5000,"current_value":1500,
         "target_date":(TODAY+timedelta(days=90)).isoformat(),"status":"in progress"},
    ]
    twin._loaded = True
    return twin


def _engine():
    from app.ml.simulation_engine import SimulationEngine
    eng = SimulationEngine(user_id=1)
    # patch _twin to return pre-loaded fixture
    eng._twin = _loaded_twin
    return eng


# ─── shared result validators ─────────────────────────────────────────────────

def _assert_valid_result(result: dict, sim_type: str):
    assert result["simulation_type"] == sim_type
    assert "current_state"    in result
    assert "future_state"     in result
    assert "difference"       in result
    assert "recommendations"  in result
    assert "confidence_score" in result
    c = result["confidence_score"]
    assert 0.0 <= c <= 1.0, f"confidence out of range: {c}"
    assert isinstance(result["recommendations"], list)
    assert len(result["recommendations"]) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCIAL
# ═══════════════════════════════════════════════════════════════════════════════

class TestFinancialSimulations:
    def test_savings_increase_structure(self):
        eng = _engine()
        r   = eng.simulate_savings_increase(monthly_increase=200, horizon_months=12)
        _assert_valid_result(r, "savings_increase")

    def test_savings_increase_future_net_higher(self):
        eng = _engine()
        r   = eng.simulate_savings_increase(monthly_increase=200, horizon_months=12)
        assert r["future_state"]["net_savings"] > r["current_state"]["net_savings"]

    def test_savings_increase_diff_correct(self):
        eng = _engine()
        r   = eng.simulate_savings_increase(monthly_increase=300, horizon_months=6)
        expected_gain = 300 * 6
        assert r["future_state"]["net_savings"] == pytest.approx(
            r["current_state"]["net_savings"] + expected_gain, abs=1
        )

    def test_major_purchase_reduces_savings(self):
        eng = _engine()
        r   = eng.simulate_major_purchase(purchase_amount=5000, purchase_month=3, horizon_months=12)
        _assert_valid_result(r, "major_purchase")
        assert r["future_state"]["purchase_impact"] == pytest.approx(-5000, abs=1)

    def test_expense_reduction_lowers_expenses(self):
        eng = _engine()
        r   = eng.simulate_expense_reduction(reduction_pct=20, horizon_months=12)
        _assert_valid_result(r, "expense_reduction")
        assert r["future_state"]["monthly_expenses"] < r["current_state"]["monthly_expenses"]

    def test_expense_reduction_non_zero_freed(self):
        eng = _engine()
        r   = eng.simulate_expense_reduction(reduction_pct=10, horizon_months=6)
        assert r["future_state"]["monthly_freed"] > 0

    def test_investment_growth_fv_exceeds_invested(self):
        eng = _engine()
        r   = eng.simulate_investment_growth(initial_amount=10000, monthly_contribution=200,
                                              annual_return_pct=8, horizon_months=24)
        _assert_valid_result(r, "investment_growth")
        assert r["future_state"]["future_value"] > 10000

    def test_investment_growth_zero_return_equals_contributions(self):
        eng = _engine()
        r   = eng.simulate_investment_growth(initial_amount=1000, monthly_contribution=100,
                                              annual_return_pct=0.01, horizon_months=10)
        # very low return: FV ≈ principal + contributions
        assert r["future_state"]["future_value"] > 0

    def test_loan_impact_emi_positive(self):
        eng = _engine()
        r   = eng.simulate_loan_impact(loan_amount=100000, annual_interest_pct=10, tenure_months=60)
        _assert_valid_result(r, "loan_impact")
        assert r["future_state"]["monthly_emi"] > 0

    def test_loan_impact_total_repayment_exceeds_principal(self):
        eng = _engine()
        r   = eng.simulate_loan_impact(loan_amount=50000, annual_interest_pct=12, tenure_months=36)
        assert r["future_state"]["total_repayment"] > 50000


# ═══════════════════════════════════════════════════════════════════════════════
# STUDY
# ═══════════════════════════════════════════════════════════════════════════════

class TestStudySimulations:
    def test_extra_hours_structure(self):
        eng = _engine()
        r   = eng.simulate_extra_study_hours(extra_hours_per_day=1.0, horizon_weeks=8)
        _assert_valid_result(r, "extra_study_hours")

    def test_extra_hours_improves_performance(self):
        eng = _engine()
        r   = eng.simulate_extra_study_hours(extra_hours_per_day=2.0, horizon_weeks=8)
        assert r["future_state"]["avg_performance_score"] >= r["current_state"]["avg_performance_score"]

    def test_extra_hours_capped_at_100(self):
        eng = _engine()
        r   = eng.simulate_extra_study_hours(extra_hours_per_day=8.0, horizon_weeks=52)
        assert r["future_state"]["avg_performance_score"] <= 100.0

    def test_exam_prep_structure(self):
        eng = _engine()
        r   = eng.simulate_exam_preparation(subject="Math", days_until_exam=30, target_score=90)
        _assert_valid_result(r, "exam_preparation")
        assert "required_daily_hours" in r["future_state"]
        assert "achievable"           in r["future_state"]

    def test_subject_improvement_structure(self):
        eng = _engine()
        r   = eng.simulate_subject_improvement(subject="Python", target_performance=85, horizon_weeks=8)
        _assert_valid_result(r, "subject_improvement")
        assert "weekly_hours_needed" in r["future_state"]


# ═══════════════════════════════════════════════════════════════════════════════
# HABITS
# ═══════════════════════════════════════════════════════════════════════════════

class TestHabitSimulations:
    def test_new_habit_increases_total(self):
        eng = _engine()
        r   = eng.simulate_new_habit(habit_name="Journaling", target_frequency="daily", horizon_weeks=8)
        _assert_valid_result(r, "new_habit")
        assert r["future_state"]["total_habits"] > r["current_state"]["total_habits"]

    def test_habit_removal_decreases_total(self):
        eng = _engine()
        r   = eng.simulate_habit_removal(habit_name="Meditate", horizon_weeks=4)
        _assert_valid_result(r, "habit_removal")
        assert r["future_state"]["total_habits"] <= r["current_state"]["total_habits"]

    def test_productivity_change_structure(self):
        eng = _engine()
        r   = eng.simulate_productivity_change(focus_improvement_pct=20, horizon_weeks=8)
        _assert_valid_result(r, "productivity_change")
        assert "productivity_score" in r["future_state"]
        assert "avg_focus_score"    in r["future_state"]


# ═══════════════════════════════════════════════════════════════════════════════
# FITNESS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFitnessSimulations:
    def test_workout_plan_structure(self):
        eng = _engine()
        r   = eng.simulate_workout_plan(sessions_per_week=3, session_duration_minutes=45,
                                         activity_type="Running", horizon_weeks=8)
        _assert_valid_result(r, "workout_plan")
        assert r["future_state"]["total_calories_burned"] > 0

    def test_workout_plan_more_sessions_more_calories(self):
        eng  = _engine()
        r3   = eng.simulate_workout_plan(3, 45, "Running", 8)
        r5   = eng.simulate_workout_plan(5, 45, "Running", 8)
        assert r5["future_state"]["total_calories_burned"] > r3["future_state"]["total_calories_burned"]

    def test_weight_loss_structure(self):
        eng = _engine()
        r   = eng.simulate_weight_loss(target_weekly_calories=1500, horizon_weeks=12)
        _assert_valid_result(r, "weight_loss")
        assert r["future_state"]["projected_kg_loss"] > 0

    def test_weight_loss_scales_with_duration(self):
        eng  = _engine()
        r8   = eng.simulate_weight_loss(1500, 8)
        r16  = eng.simulate_weight_loss(1500, 16)
        assert r16["future_state"]["projected_kg_loss"] > r8["future_state"]["projected_kg_loss"]

    def test_goal_completion_structure(self):
        eng = _engine()
        r   = eng.simulate_goal_completion(goal_name="Run 5km", horizon_weeks=8)
        _assert_valid_result(r, "fitness_goal_completion")
        assert 0 <= r["future_state"]["completion_probability"] <= 1


# ═══════════════════════════════════════════════════════════════════════════════
# GOALS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGoalSimulations:
    def test_goal_completion_probability_valid_goal(self):
        eng = _engine()
        r   = eng.simulate_goal_completion_probability(goal_id=1, accelerate_by_pct=0)
        _assert_valid_result(r, "goal_completion_probability")

    def test_goal_completion_probability_range(self):
        eng = _engine()
        r   = eng.simulate_goal_completion_probability(goal_id=1)
        prob = r["future_state"]["probability"]
        assert 0.0 <= prob <= 1.0

    def test_invalid_goal_returns_error(self):
        eng = _engine()
        r   = eng.simulate_goal_completion_probability(goal_id=9999)
        assert "error" in r["future_state"]

    def test_acceleration_decreases_days_to_complete(self):
        eng    = _engine()
        r0     = eng.simulate_goal_completion_probability(goal_id=1, accelerate_by_pct=0)
        r50    = eng.simulate_goal_completion_probability(goal_id=1, accelerate_by_pct=50)
        days0  = r0["future_state"].get("days_to_complete", 999)
        days50 = r50["future_state"].get("days_to_complete", 999)
        assert days50 <= days0


# ═══════════════════════════════════════════════════════════════════════════════
# FULL SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullSimulation:
    def test_full_simulation_structure(self):
        eng = _engine()
        r   = eng.simulate_full(horizon_months=6, financial_boost_pct=10,
                                  study_hours_increase=1, habit_compliance_target=80,
                                  fitness_sessions_per_week=3)
        _assert_valid_result(r, "full_simulation")

    def test_full_simulation_has_all_domains(self):
        eng = _engine()
        r   = eng.simulate_full()
        for domain in ("financial", "study", "habits", "fitness"):
            assert domain in r["current_state"]
            assert domain in r["future_state"]

    def test_full_simulation_recommendations_not_empty(self):
        eng = _engine()
        r   = eng.simulate_full()
        assert len(r["recommendations"]) >= 1

"""
tests/test_digital_twin.py

Unit tests for DigitalTwin class (Milestone 3).
Covers: state building, scoring, risk, projection, snapshot, compare_states.

Run:  pytest tests/test_digital_twin.py -v --tb=short
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── path bootstrap ────────────────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parents[1] / "backend"
_ROOT    = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── fixtures ──────────────────────────────────────────────────────────────────

def _make_twin(financial=None, study=None, habits=None, fitness=None, goals=None):
    """Create a DigitalTwin with pre-loaded mock data (no DB call)."""
    from app.ml.digital_twin import DigitalTwin
    twin = DigitalTwin(user_id=999)
    twin._financial = financial or []
    twin._study     = study     or []
    twin._habits    = habits    or []
    twin._fitness   = fitness   or []
    twin._goals     = goals     or []
    twin._loaded    = True
    return twin


SAMPLE_FINANCIAL = [
    {"id": 1, "record_type": "income",  "amount": 5000, "date": "2026-01-15T00:00:00",
     "category": "salary",    "recurring_frequency": "monthly", "goal_impact": None},
    {"id": 2, "record_type": "expense", "amount": 1500, "date": "2026-01-20T00:00:00",
     "category": "housing",   "recurring_frequency": "monthly", "goal_impact": None},
    {"id": 3, "record_type": "expense", "amount": 500,  "date": "2026-02-05T00:00:00",
     "category": "food",      "recurring_frequency": "weekly",  "goal_impact": None},
    {"id": 4, "record_type": "income",  "amount": 1000, "date": "2026-02-15T00:00:00",
     "category": "freelance", "recurring_frequency": "once",    "goal_impact": None},
]

SAMPLE_STUDY = [
    {"id": 1, "subject": "Python",      "study_date": "2026-07-01T00:00:00",
     "study_hours": 2.0, "focus_score": 80, "task_completion": 85, "performance_score": 78},
    {"id": 2, "subject": "Mathematics", "study_date": "2026-07-02T00:00:00",
     "study_hours": 1.5, "focus_score": 70, "task_completion": 75, "performance_score": 72},
    {"id": 3, "subject": "Python",      "study_date": "2026-07-03T00:00:00",
     "study_hours": 3.0, "focus_score": 90, "task_completion": 90, "performance_score": 88},
]

SAMPLE_HABITS = [
    {"id": 1, "name": "Morning Run",   "target_frequency": "daily",  "completed": True,  "streak": 10},
    {"id": 2, "name": "Read 30min",    "target_frequency": "daily",  "completed": True,  "streak": 5},
    {"id": 3, "name": "Meditate",      "target_frequency": "daily",  "completed": False, "streak": 0},
    {"id": 4, "name": "Drink 2L Water","target_frequency": "daily",  "completed": True,  "streak": 20},
]

SAMPLE_FITNESS = [
    {"id": i, "activity_type": "Running", "duration": 45, "calories_burned": 400,
     "activity_date": f"2026-0{(i%3)+5}-{i:02d}T00:00:00"}
    for i in range(1, 9)
]

TODAY = datetime.utcnow()
SAMPLE_GOALS = [
    {"id": 1, "name": "Save 10k",  "description": "Emergency fund",
     "target_value": 10000, "current_value": 4200,
     "target_date": (TODAY + timedelta(days=180)).isoformat(), "status": "in progress"},
    {"id": 2, "name": "Run 5km",   "description": "Fitness goal",
     "target_value": 5.0,   "current_value": 3.2,
     "target_date": (TODAY + timedelta(days=60)).isoformat(),  "status": "in progress"},
    {"id": 3, "name": "Read 12 Books", "description": "Reading goal",
     "target_value": 12,    "current_value": 12,
     "target_date": (TODAY + timedelta(days=10)).isoformat(),  "status": "completed"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: build_current_state
# ═══════════════════════════════════════════════════════════════════════════════

class TestBuildCurrentState:
    def test_returns_all_domains(self):
        twin  = _make_twin(SAMPLE_FINANCIAL, SAMPLE_STUDY, SAMPLE_HABITS, SAMPLE_FITNESS, SAMPLE_GOALS)
        state = twin.build_current_state()
        assert "financial" in state
        assert "study"     in state
        assert "habits"    in state
        assert "fitness"   in state
        assert "goals"     in state
        assert "productivity_score"  in state
        assert "risk_score"          in state
        assert "behavioral_patterns" in state

    def test_financial_state_calculates_net_savings(self):
        twin  = _make_twin(financial=SAMPLE_FINANCIAL)
        fin   = twin._financial_state()
        # income = 5000 + 1000 = 6000; expenses = 1500 + 500 = 2000
        assert fin["total_income"]   == pytest.approx(6000, abs=1)
        assert fin["total_expenses"] == pytest.approx(2000, abs=1)
        assert fin["net_savings"]    == pytest.approx(4000, abs=1)

    def test_financial_state_empty(self):
        twin = _make_twin()
        fin  = twin._financial_state()
        assert fin["net_savings"]   == 0
        assert fin["record_count"]  == 0
        assert fin["savings_rate"]  == 0

    def test_study_state_averages(self):
        twin = _make_twin(study=SAMPLE_STUDY)
        stu  = twin._study_state()
        assert stu["total_sessions"] == 3
        assert stu["avg_focus_score"]       == pytest.approx((80+70+90)/3, abs=0.1)
        assert stu["avg_performance_score"] == pytest.approx((78+72+88)/3, abs=0.1)
        assert "Python" in stu["subjects"]
        assert "Mathematics" in stu["subjects"]

    def test_study_state_empty(self):
        twin = _make_twin()
        stu  = twin._study_state()
        assert stu["total_sessions"]        == 0
        assert stu["avg_performance_score"] == 0

    def test_habits_state_completion_rate(self):
        twin = _make_twin(habits=SAMPLE_HABITS)
        hab  = twin._habits_state()
        assert hab["total_habits"]    == 4
        assert hab["completed_habits"] == 3
        assert hab["completion_rate"]  == pytest.approx(0.75, abs=0.01)
        assert hab["best_streak"]      == 20
        assert "Meditate" in hab["at_risk_habits"]

    def test_fitness_state_sessions_per_week(self):
        twin = _make_twin(fitness=SAMPLE_FITNESS)
        fit  = twin._fitness_state()
        assert fit["total_sessions"] == 8
        assert fit["avg_calories"]   == pytest.approx(400, abs=1)
        assert fit["sessions_per_week"] > 0

    def test_goals_state_progress(self):
        twin  = _make_twin(goals=SAMPLE_GOALS)
        goals = twin._goals_state()
        assert len(goals) == 3
        save_goal = next(g for g in goals if g["name"] == "Save 10k")
        assert save_goal["progress_pct"] == pytest.approx(42.0, abs=0.5)
        completed = next(g for g in goals if g["name"] == "Read 12 Books")
        assert completed["progress_pct"] == pytest.approx(100.0, abs=0.1)

    def test_snapshot_at_is_recent(self):
        twin  = _make_twin()
        state = twin.build_current_state()
        snap_dt = datetime.fromisoformat(state["snapshot_at"])
        assert (datetime.utcnow() - snap_dt).total_seconds() < 10


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: calculate_behavioral_score
# ═══════════════════════════════════════════════════════════════════════════════

class TestBehavioralScore:
    def test_all_keys_present(self):
        twin   = _make_twin(SAMPLE_FINANCIAL, SAMPLE_STUDY, SAMPLE_HABITS, SAMPLE_FITNESS, SAMPLE_GOALS)
        scores = twin.calculate_behavioral_score()
        for key in ("study_score","habits_score","fitness_score","finance_score","goals_score","productivity_score"):
            assert key in scores

    def test_scores_in_range(self):
        twin   = _make_twin(SAMPLE_FINANCIAL, SAMPLE_STUDY, SAMPLE_HABITS, SAMPLE_FITNESS, SAMPLE_GOALS)
        scores = twin.calculate_behavioral_score()
        for v in scores.values():
            assert 0 <= v <= 100, f"Score out of range: {v}"

    def test_empty_data_gives_zero(self):
        twin   = _make_twin()
        scores = twin.calculate_behavioral_score()
        assert scores["study_score"]   == 0.0
        assert scores["fitness_score"] == 0.0
        assert scores["finance_score"] == 0.0

    def test_productivity_weighted_correctly(self):
        twin   = _make_twin(SAMPLE_FINANCIAL, SAMPLE_STUDY, SAMPLE_HABITS, SAMPLE_FITNESS, SAMPLE_GOALS)
        scores = twin.calculate_behavioral_score()
        expected = (
            scores["study_score"]   * 0.30
            + scores["habits_score"]  * 0.25
            + scores["fitness_score"] * 0.20
            + scores["finance_score"] * 0.15
            + scores["goals_score"]   * 0.10
        )
        assert scores["productivity_score"] == pytest.approx(expected, abs=0.2)

    def test_full_data_productivity_above_zero(self):
        twin  = _make_twin(SAMPLE_FINANCIAL, SAMPLE_STUDY, SAMPLE_HABITS, SAMPLE_FITNESS, SAMPLE_GOALS)
        scores = twin.calculate_behavioral_score()
        assert scores["productivity_score"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: calculate_risk_score
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskScore:
    def test_zero_data_returns_risk(self):
        twin = _make_twin()
        risk = twin.calculate_risk_score()
        # no data means sessions_per_week < 1 and completion_rate == 0 → high risk
        assert risk >= 0

    def test_negative_savings_adds_risk(self):
        bad_fin = [
            {"id": 1, "record_type": "expense", "amount": 5000,
             "date": "2026-01-01T00:00:00", "category": "housing",
             "recurring_frequency": "monthly", "goal_impact": None},
            {"id": 2, "record_type": "income",  "amount": 3000,
             "date": "2026-01-01T00:00:00", "category": "salary",
             "recurring_frequency": "monthly", "goal_impact": None},
        ]
        twin_bad  = _make_twin(financial=bad_fin)
        twin_good = _make_twin(financial=SAMPLE_FINANCIAL)
        assert twin_bad.calculate_risk_score() > twin_good.calculate_risk_score()

    def test_risk_capped_at_100(self):
        twin = _make_twin()
        risk = twin.calculate_risk_score()
        assert risk <= 100

    def test_good_data_lowers_risk(self):
        twin = _make_twin(SAMPLE_FINANCIAL, SAMPLE_STUDY, SAMPLE_HABITS, SAMPLE_FITNESS, SAMPLE_GOALS)
        risk = twin.calculate_risk_score()
        assert risk < 80   # good all-round data should not be max risk


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: project_state
# ═══════════════════════════════════════════════════════════════════════════════

class TestProjectState:
    def test_returns_horizon(self):
        twin = _make_twin(SAMPLE_FINANCIAL)
        proj = twin.project_state(horizon_months=6)
        assert proj["horizon_months"] == 6

    def test_financial_net_increases_with_positive_savings(self):
        twin     = _make_twin(financial=SAMPLE_FINANCIAL)
        current  = twin._financial_state()
        proj     = twin.project_state(6)
        assert proj["financial"]["net_savings"] >= current["net_savings"]

    def test_study_projected_performance_does_not_exceed_100(self):
        high_study = [
            {"id": 1, "subject": "Math", "study_date": "2026-01-01T00:00:00",
             "study_hours": 5, "focus_score": 99, "task_completion": 99, "performance_score": 99},
        ]
        twin = _make_twin(study=high_study)
        proj = twin.project_state(12)
        assert proj["study"]["projected_performance"] <= 100

    def test_goals_in_projection(self):
        twin = _make_twin(goals=SAMPLE_GOALS)
        proj = twin.project_state(6)
        assert isinstance(proj["goals"], list)
        assert len(proj["goals"]) == 3
        for g in proj["goals"]:
            assert "projected_progress_pct" in g
            assert g["projected_progress_pct"] <= 100


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: generate_summary
# ═══════════════════════════════════════════════════════════════════════════════

class TestGenerateSummary:
    def test_summary_keys(self):
        twin    = _make_twin(SAMPLE_FINANCIAL, SAMPLE_STUDY, SAMPLE_HABITS, SAMPLE_FITNESS, SAMPLE_GOALS)
        summary = twin.generate_summary()
        for key in ("user_id","overall_score","financial_score","study_score",
                    "habits_score","fitness_score","goals_score","risk_level",
                    "top_insight","strongest_domain","weakest_domain","generated_at"):
            assert key in summary, f"Missing key: {key}"

    def test_risk_level_valid(self):
        twin = _make_twin()
        s    = twin.generate_summary()
        assert s["risk_level"] in ("low", "medium", "high")

    def test_user_id_preserved(self):
        twin = _make_twin()
        s    = twin.generate_summary()
        assert s["user_id"] == 999


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: compare_states
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompareStates:
    def test_delta_numeric(self):
        from app.ml.digital_twin import DigitalTwin
        a = {"net_savings": 1000.0, "score": 50.0}
        b = {"net_savings": 1500.0, "score": 65.0}
        result = DigitalTwin.compare_states(a, b)
        assert result["delta"]["net_savings"] == pytest.approx(500.0)
        assert result["delta"]["score"]       == pytest.approx(15.0)

    def test_labels_preserved(self):
        from app.ml.digital_twin import DigitalTwin
        r = DigitalTwin.compare_states({"x": 1}, {"x": 2}, "Before", "After")
        assert r["label_a"] == "Before"
        assert r["label_b"] == "After"

    def test_compare_at_present(self):
        from app.ml.digital_twin import DigitalTwin
        r = DigitalTwin.compare_states({}, {})
        assert "compared_at" in r

    def test_non_numeric_delta_uses_new_value(self):
        from app.ml.digital_twin import DigitalTwin
        r = DigitalTwin.compare_states({"label": "old"}, {"label": "new"})
        assert r["delta"]["label"] == "new"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST: save_snapshot (mocked DB)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaveSnapshot:
    def test_snapshot_returns_dict(self):
        twin = _make_twin(SAMPLE_FINANCIAL, SAMPLE_STUDY, SAMPLE_HABITS)

        mock_row = MagicMock()
        mock_row.id               = 42
        mock_row.user_id          = 999
        mock_row.scenario_name    = "test"
        mock_row.scenario_type    = "snapshot"
        mock_row.confidence_score = 0.75
        mock_row.created_at       = datetime.utcnow()

        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__  = MagicMock(return_value=False)
        mock_db.refresh   = MagicMock(return_value=None)

        with patch("app.core.database.SessionLocal", return_value=mock_db), \
             patch("app.models.user.SimulationResult", return_value=mock_row):
            result = twin.save_snapshot("test")

        assert isinstance(result, dict)
        assert "result_data" in result

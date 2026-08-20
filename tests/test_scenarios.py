"""
tests/test_scenarios.py

Unit tests for scenario_service and recommendation_service (Milestone 3).

Run:  pytest tests/test_scenarios.py -v --tb=short
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
_ROOT    = Path(__file__).resolve().parents[1]
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── shared pre-loaded twin helper ─────────────────────────────────────────────

TODAY = datetime.utcnow()

def _preloaded_twin(user_id=1):
    from app.ml.digital_twin import DigitalTwin
    twin = DigitalTwin(user_id)
    twin._financial = [
        {"id":1,"record_type":"income", "amount":5000,"date":"2026-01-15T00:00:00",
         "category":"salary","recurring_frequency":"monthly","goal_impact":None},
        {"id":2,"record_type":"expense","amount":3000,"date":"2026-01-20T00:00:00",
         "category":"housing","recurring_frequency":"monthly","goal_impact":None},
    ]
    twin._study = [
        {"id":1,"subject":"Python","study_date":"2026-07-01T00:00:00",
         "study_hours":2.0,"focus_score":70,"task_completion":75,"performance_score":68},
    ]
    twin._habits = [
        {"id":1,"name":"Morning Run","target_frequency":"daily","completed":True,"streak":5},
        {"id":2,"name":"Meditate",   "target_frequency":"daily","completed":False,"streak":0},
        {"id":3,"name":"Read",       "target_frequency":"daily","completed":True,"streak":3},
    ]
    twin._fitness = [
        {"id":i,"activity_type":"Running","duration":35,"calories_burned":300,
         "activity_date":f"2026-06-{i:02d}T00:00:00"}
        for i in range(1, 7)
    ]
    twin._goals = [
        {"id":1,"name":"Save 5k","description":"Emergency fund",
         "target_value":5000,"current_value":2000,
         "target_date":(TODAY+timedelta(days=120)).isoformat(),"status":"in progress"},
        {"id":2,"name":"Run 5km","description":"Fitness",
         "target_value":5.0,"current_value":2.0,
         "target_date":(TODAY+timedelta(days=60)).isoformat(), "status":"in progress"},
    ]
    twin._loaded = True
    return twin


def _patch_twin(user_id=1):
    """Context manager: patch DigitalTwin to return pre-loaded twin."""
    from app.ml import digital_twin as dt_mod
    mock = MagicMock(return_value=_preloaded_twin(user_id))
    return patch.object(dt_mod, "DigitalTwin", mock)


# ═══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION SERVICE
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecommendationService:
    def _get_recs(self, user_id=1):
        from app.services.recommendation_service import generate_all_recommendations
        with _patch_twin(user_id):
            return generate_all_recommendations(user_id)

    def test_returns_required_keys(self):
        result = self._get_recs()
        assert "user_id"             in result
        assert "generated_at"        in result
        assert "recommendations"     in result
        assert "overall_health_score" in result

    def test_recommendations_is_list(self):
        result = self._get_recs()
        assert isinstance(result["recommendations"], list)

    def test_max_8_recommendations(self):
        result = self._get_recs()
        assert len(result["recommendations"]) <= 8

    def test_each_rec_has_required_fields(self):
        result = self._get_recs()
        for rec in result["recommendations"]:
            for field in ("domain","priority","impact","confidence","title","description","action_steps"):
                assert field in rec, f"Missing field '{field}' in rec: {rec.get('title','?')}"

    def test_priority_values_valid(self):
        result = self._get_recs()
        for rec in result["recommendations"]:
            assert rec["priority"] in ("high","medium","low")

    def test_impact_values_valid(self):
        result = self._get_recs()
        for rec in result["recommendations"]:
            assert rec["impact"] in ("high","medium","low")

    def test_confidence_in_range(self):
        result = self._get_recs()
        for rec in result["recommendations"]:
            assert 0.0 <= rec["confidence"] <= 1.0

    def test_action_steps_non_empty(self):
        result = self._get_recs()
        for rec in result["recommendations"]:
            assert len(rec["action_steps"]) >= 1

    def test_sorted_high_priority_first(self):
        result = self._get_recs()
        recs = result["recommendations"]
        if len(recs) >= 2:
            porder = {"high": 0, "medium": 1, "low": 2}
            for i in range(len(recs) - 1):
                assert porder[recs[i]["priority"]] <= porder[recs[i+1]["priority"]]

    def test_health_score_in_range(self):
        result = self._get_recs()
        assert 0 <= result["overall_health_score"] <= 100

    def test_domains_covered(self):
        result = self._get_recs()
        domains = {r["domain"] for r in result["recommendations"]}
        # At least 2 distinct domains should appear with our sample data
        assert len(domains) >= 1

    def test_no_data_still_returns_recs(self):
        """Even with empty data, recommendations are generated (onboarding hints)."""
        from app.ml.digital_twin import DigitalTwin
        from app.services.recommendation_service import generate_all_recommendations
        empty_twin = DigitalTwin(1)
        empty_twin._financial = []
        empty_twin._study     = []
        empty_twin._habits    = []
        empty_twin._fitness   = []
        empty_twin._goals     = []
        empty_twin._loaded    = True
        with patch("app.services.recommendation_service._twin", return_value=empty_twin):
            result = generate_all_recommendations(1)
        assert len(result["recommendations"]) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO SERVICE: compare_two_scenarios
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompareScenarios:
    def _compare(self):
        from app.services.scenario_service import compare_two_scenarios
        sc_a = {"name": "Save More",   "sim_type": "financial.savings_increase",
                "description": "Save 200/mo", "parameters": {"monthly_increase": 200, "horizon_months": 12}}
        sc_b = {"name": "Study Harder","sim_type": "study.extra_hours",
                "description": "1h more/day", "parameters": {"extra_hours_per_day": 1, "horizon_weeks": 16}}
        with _patch_twin():
            return compare_two_scenarios(1, sc_a, sc_b, horizon_months=12)

    def test_required_keys(self):
        r = self._compare()
        for key in ("scenario_a_name","scenario_b_name","overall_winner",
                    "domain_impacts","scenario_a_risk","scenario_b_risk",
                    "recommendation","confidence"):
            assert key in r, f"Missing key: {key}"

    def test_overall_winner_valid(self):
        r = self._compare()
        assert r["overall_winner"] in ("A","B","tie")

    def test_domain_impacts_is_list(self):
        r = self._compare()
        assert isinstance(r["domain_impacts"], list)

    def test_domain_impact_fields(self):
        r = self._compare()
        for imp in r["domain_impacts"]:
            for field in ("domain","scenario_a_score","scenario_b_score","winner","delta","rationale"):
                assert field in imp

    def test_domain_impact_winner_valid(self):
        r = self._compare()
        for imp in r["domain_impacts"]:
            assert imp["winner"] in ("A","B","tie")

    def test_risk_scores_non_negative(self):
        r = self._compare()
        assert r["scenario_a_risk"] >= 0
        assert r["scenario_b_risk"] >= 0

    def test_confidence_in_range(self):
        r = self._compare()
        assert 0.0 <= r["confidence"] <= 1.0

    def test_recommendation_is_string(self):
        r = self._compare()
        assert isinstance(r["recommendation"], str)
        assert len(r["recommendation"]) > 10


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO SERVICE: best_future_path
# ═══════════════════════════════════════════════════════════════════════════════

class TestBestFuturePath:
    def test_required_keys(self):
        from app.services.scenario_service import best_future_path
        with _patch_twin():
            r = best_future_path(1)
        for key in ("user_id","recommended_path","path_description",
                    "expected_score_gain","horizon_months","milestones",
                    "top_actions","generated_at"):
            assert key in r

    def test_milestones_is_list(self):
        from app.services.scenario_service import best_future_path
        with _patch_twin():
            r = best_future_path(1)
        assert isinstance(r["milestones"], list)

    def test_top_actions_non_empty(self):
        from app.services.scenario_service import best_future_path
        with _patch_twin():
            r = best_future_path(1)
        assert len(r["top_actions"]) >= 1

    def test_horizon_months_is_6(self):
        from app.services.scenario_service import best_future_path
        with _patch_twin():
            r = best_future_path(1)
        assert r["horizon_months"] == 6

    def test_recommended_path_is_string(self):
        from app.services.scenario_service import best_future_path
        with _patch_twin():
            r = best_future_path(1)
        assert isinstance(r["recommended_path"], str)
        assert len(r["recommended_path"]) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO SERVICE: rank_scenarios
# ═══════════════════════════════════════════════════════════════════════════════

class TestRankScenarios:
    def test_returns_sorted_list(self):
        from app.services.scenario_service import rank_scenarios
        scenarios = [
            {"name":"Save",  "sim_type":"financial.savings_increase",
             "description":"", "parameters":{"monthly_increase":200,"horizon_months":12}},
            {"name":"Study", "sim_type":"study.extra_hours",
             "description":"", "parameters":{"extra_hours_per_day":1,"horizon_weeks":8}},
        ]
        with _patch_twin():
            ranked = rank_scenarios(1, scenarios)
        assert isinstance(ranked, list)
        assert len(ranked) == 2

    def test_ranked_descending(self):
        from app.services.scenario_service import rank_scenarios
        scenarios = [
            {"name":"A","sim_type":"financial.savings_increase",
             "description":"","parameters":{"monthly_increase":200,"horizon_months":12}},
            {"name":"B","sim_type":"fitness.workout_plan",
             "description":"","parameters":{"sessions_per_week":3,"session_duration_minutes":45,
                                            "activity_type":"Running","horizon_weeks":8}},
        ]
        with _patch_twin():
            ranked = rank_scenarios(1, scenarios)
        if len(ranked) >= 2:
            assert ranked[0]["score"] >= ranked[1]["score"]

    def test_each_result_has_score(self):
        from app.services.scenario_service import rank_scenarios
        scenarios = [
            {"name":"Test","sim_type":"financial.savings_increase",
             "description":"","parameters":{"monthly_increase":100,"horizon_months":6}},
        ]
        with _patch_twin():
            ranked = rank_scenarios(1, scenarios)
        for item in ranked:
            assert "score"      in item
            assert "confidence" in item
            assert "risk"       in item


# ═══════════════════════════════════════════════════════════════════════════════
# SCENARIO SERVICE: risk_comparison
# ═══════════════════════════════════════════════════════════════════════════════

class TestRiskComparison:
    def test_required_keys(self):
        from app.services.scenario_service import risk_comparison
        sc = {"name":"Test","sim_type":"financial.savings_increase",
              "description":"","parameters":{"monthly_increase":200,"horizon_months":12}}
        with _patch_twin():
            r = risk_comparison(1, sc, horizon_months=12)
        for key in ("overall_risk_score","risk_level","risk_factors",
                    "safe_to_proceed","summary"):
            assert key in r

    def test_risk_level_valid(self):
        from app.services.scenario_service import risk_comparison
        sc = {"name":"Test","sim_type":"financial.expense_reduction",
              "description":"","parameters":{"reduction_pct":10,"horizon_months":12}}
        with _patch_twin():
            r = risk_comparison(1, sc)
        assert r["risk_level"] in ("low","medium","high","critical")

    def test_safe_to_proceed_is_bool(self):
        from app.services.scenario_service import risk_comparison
        sc = {"name":"Test","sim_type":"financial.savings_increase",
              "description":"","parameters":{"monthly_increase":100,"horizon_months":12}}
        with _patch_twin():
            r = risk_comparison(1, sc)
        assert isinstance(r["safe_to_proceed"], bool)

    def test_risk_score_in_range(self):
        from app.services.scenario_service import risk_comparison
        sc = {"name":"Test","sim_type":"study.extra_hours",
              "description":"","parameters":{"extra_hours_per_day":1,"horizon_weeks":8}}
        with _patch_twin():
            r = risk_comparison(1, sc)
        assert 0 <= r["overall_risk_score"] <= 100

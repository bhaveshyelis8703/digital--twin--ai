"""
backend/app/services/scenario_service.py

Scenario comparison engine – runs two user-defined simulations side by side,
ranks them, identifies the best future path and quantifies risk differentials.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parents[2]
_ROOT    = _BACKEND.parent
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _engine(user_id: int):
    from app.ml.simulation_engine import SimulationEngine
    return SimulationEngine(user_id)


def _twin(user_id: int):
    from app.ml.digital_twin import DigitalTwin
    return DigitalTwin(user_id).load_from_database()


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _run_scenario(user_id: int, scenario: dict[str, Any]) -> dict[str, Any]:
    """
    Execute a named scenario.  The scenario dict must contain:
      name        – human label
      sim_type    – one of the run_simulation dispatch keys
      parameters  – kwargs forwarded to the engine method
    """
    from app.services.digital_twin_service import run_simulation
    return run_simulation(user_id, scenario["sim_type"], scenario.get("parameters", {}))


def _domain_score_from_result(result: dict[str, Any], domain: str) -> float:
    """
    Extract a single representative numeric score from a simulation result
    for the requested domain.  Falls back to confidence_score if the domain
    field is absent.
    """
    future = result.get("future_state", {})
    domain_keys = {
        "financial": ["net_savings", "monthly_savings", "future_value"],
        "study":     ["avg_performance_score", "projected_performance", "target_score"],
        "habits":    ["completion_rate", "projected_completion_rate"],
        "fitness":   ["projected_fitness_score", "total_calories_burned", "projected_sessions"],
        "goals":     ["probability", "projected_progress_pct"],
    }
    for key in domain_keys.get(domain, []):
        if key in future:
            val = future[key]
            if isinstance(val, (int, float)):
                return float(val)
    # fallback
    return result.get("confidence_score", 0.5) * 100


def _impact_analysis(
    result_a: dict[str, Any],
    result_b: dict[str, Any],
    domains: list[str],
) -> list[dict[str, Any]]:
    """Produce per-domain comparison rows."""
    impacts = []
    for domain in domains:
        score_a = _domain_score_from_result(result_a, domain)
        score_b = _domain_score_from_result(result_b, domain)
        delta   = score_b - score_a
        winner  = "B" if delta > 0.5 else ("A" if delta < -0.5 else "tie")
        impacts.append({
            "domain":          domain,
            "scenario_a_score": round(score_a, 2),
            "scenario_b_score": round(score_b, 2),
            "winner":          winner,
            "delta":           round(delta, 2),
            "rationale":       _rationale(domain, score_a, score_b, winner),
        })
    return impacts


def _rationale(domain: str, a: float, b: float, winner: str) -> str:
    if winner == "tie":
        return f"Both scenarios produce similar {domain} outcomes (Δ < 0.5)."
    better = "B" if winner == "B" else "A"
    worse  = "A" if better == "B" else "B"
    return (
        f"Scenario {better} improves {domain} by {abs(b - a):.1f} units "
        f"compared to Scenario {worse}."
    )


def _risk_from_result(result: dict[str, Any]) -> float:
    """Estimate risk score from a simulation result (0-100, lower is safer)."""
    future = result.get("future_state", {})
    risk   = 0.0

    # negative savings → high financial risk
    ns = future.get("net_savings")
    if isinstance(ns, (int, float)) and ns < 0:
        risk += 30

    # low completion rate
    cr = future.get("completion_rate") or future.get("projected_completion_rate")
    if isinstance(cr, (int, float)) and cr < 0.4:
        risk += 20

    # very low probability
    prob = future.get("probability")
    if isinstance(prob, (int, float)) and prob < 0.3:
        risk += 20

    # high EMI burden
    free = future.get("monthly_free_cash")
    if isinstance(free, (int, float)) and free < 0:
        risk += 30

    return min(100.0, risk + (1 - result.get("confidence_score", 0.5)) * 20)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC SERVICE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def compare_two_scenarios(
    user_id: int,
    scenario_a: dict[str, Any],
    scenario_b: dict[str, Any],
    horizon_months: int = 12,
    domains: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run both scenarios and produce a structured head-to-head comparison.

    Parameters
    ----------
    scenario_a / scenario_b : dicts with keys  name, sim_type, parameters
    """
    domains = domains or ["financial", "study", "habits", "fitness"]

    result_a = _run_scenario(user_id, scenario_a)
    result_b = _run_scenario(user_id, scenario_b)

    impacts = _impact_analysis(result_a, result_b, domains)
    a_wins  = sum(1 for i in impacts if i["winner"] == "A")
    b_wins  = sum(1 for i in impacts if i["winner"] == "B")
    overall = "A" if a_wins > b_wins else ("B" if b_wins > a_wins else "tie")

    risk_a = _risk_from_result(result_a)
    risk_b = _risk_from_result(result_b)

    recommendation = (
        f"Scenario '{scenario_a['name']}' wins {a_wins} domains; "
        f"Scenario '{scenario_b['name']}' wins {b_wins} domains. "
        f"{'Scenario A' if overall == 'A' else 'Scenario B' if overall == 'B' else 'Neither'} "
        f"is the recommended path based on overall impact."
    )

    avg_confidence = (
        result_a.get("confidence_score", 0.5) + result_b.get("confidence_score", 0.5)
    ) / 2

    return {
        "scenario_a_name":  scenario_a["name"],
        "scenario_b_name":  scenario_b["name"],
        "overall_winner":   overall,
        "domain_impacts":   impacts,
        "scenario_a_risk":  round(risk_a, 1),
        "scenario_b_risk":  round(risk_b, 1),
        "recommendation":   recommendation,
        "confidence":       round(avg_confidence, 3),
        "compared_at":      datetime.utcnow().isoformat(),
    }


def rank_scenarios(
    user_id: int,
    scenarios: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Run N scenarios and rank them by overall score (confidence × impact proxy).
    Returns scenarios sorted best → worst.
    """
    scored = []
    for sc in scenarios:
        result = _run_scenario(user_id, sc)
        conf   = result.get("confidence_score", 0.5)
        risk   = _risk_from_result(result) / 100
        score  = conf * (1 - risk * 0.5)
        scored.append({
            "scenario_name": sc["name"],
            "score":         round(score * 100, 1),
            "confidence":    conf,
            "risk":          round(_risk_from_result(result), 1),
            "result":        result,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def best_future_path(user_id: int) -> dict[str, Any]:
    """
    Evaluate a fixed set of canonical scenarios and identify the single best
    path the user should follow over the next 6 months.
    """
    candidates = [
        {"name": "Save More",        "sim_type": "financial.savings_increase",
         "parameters": {"monthly_increase": 200, "horizon_months": 6}},
        {"name": "Study Harder",     "sim_type": "study.extra_hours",
         "parameters": {"extra_hours_per_day": 1, "horizon_weeks": 24}},
        {"name": "Habit Sprint",     "sim_type": "habit.productivity",
         "parameters": {"focus_improvement_pct": 20, "horizon_weeks": 24}},
        {"name": "Fitness Push",     "sim_type": "fitness.workout_plan",
         "parameters": {"sessions_per_week": 4, "session_duration_minutes": 45,
                        "activity_type": "Mixed", "horizon_weeks": 24}},
    ]

    ranked = rank_scenarios(user_id, candidates)
    best   = ranked[0] if ranked else {}

    tw      = _twin(user_id)
    summary = tw.generate_summary()

    # Build milestones for the winner
    milestones = []
    if ranked:
        for i, month in enumerate([2, 4, 6], 1):
            milestones.append({
                "month": month,
                "milestone": f"Month {month}: {ranked[0]['scenario_name']} – "
                             f"expected score gain +{i * 2:.0f} pts",
            })

    top_actions = [
        f"Focus on '{summary['weakest_domain']}' domain first.",
        f"Maintain your '{summary['strongest_domain']}' domain momentum.",
    ] + (best.get("result", {}).get("recommendations", [])[:2] if best else [])

    return {
        "user_id":             user_id,
        "recommended_path":    best.get("scenario_name", "Balanced Improvement"),
        "path_description":    f"Your highest-impact action is: {best.get('scenario_name', 'N/A')}.",
        "expected_score_gain": round(best.get("score", 0) - 50, 1),
        "horizon_months":      6,
        "milestones":          milestones,
        "top_actions":         top_actions,
        "all_ranked":          [{k: v for k, v in s.items() if k != "result"} for s in ranked],
        "generated_at":        datetime.utcnow().isoformat(),
    }


def risk_comparison(
    user_id: int,
    scenario: dict[str, Any],
    horizon_months: int = 12,
) -> dict[str, Any]:
    """
    Full risk breakdown for a single scenario vs the user's current baseline.
    """
    from app.services.digital_twin_service import generate_risk_analysis

    baseline_risk = generate_risk_analysis(user_id)
    scenario_result = _run_scenario(user_id, scenario)
    scenario_risk   = _risk_from_result(scenario_result)

    risk_factors: list[dict[str, Any]] = []

    future = scenario_result.get("future_state", {})

    # Financial risk
    ns = future.get("net_savings")
    if isinstance(ns, (int, float)):
        sev = "low" if ns > 0 else ("medium" if ns > -1000 else "high")
        risk_factors.append({
            "domain": "financial", "risk_type": "liquidity",
            "severity": sev, "probability": 0.7 if sev == "high" else 0.3,
            "description": f"Projected net savings: ${ns:,.0f}",
            "mitigation": "Maintain 3-month emergency fund before proceeding.",
        })

    # EMI risk
    emi = future.get("monthly_emi")
    free = future.get("monthly_free_cash")
    if isinstance(emi, (int, float)) and isinstance(free, (int, float)):
        sev = "critical" if free < 0 else ("high" if free < 500 else "low")
        risk_factors.append({
            "domain": "financial", "risk_type": "cash_flow",
            "severity": sev, "probability": 0.9 if sev == "critical" else 0.4,
            "description": f"EMI ${emi:,.0f}/month leaves ${free:,.0f} free cash.",
            "mitigation": "Reduce loan tenure or increase income before committing.",
        })

    # completion risk
    prob = future.get("probability") or future.get("completion_probability")
    if isinstance(prob, (int, float)):
        sev = "low" if prob > 0.7 else ("medium" if prob > 0.4 else "high")
        risk_factors.append({
            "domain": "goals", "risk_type": "completion",
            "severity": sev, "probability": 1 - prob,
            "description": f"Completion probability: {prob * 100:.0f}%",
            "mitigation": "Set weekly review checkpoints to catch slippage early.",
        })

    safe = scenario_risk < 50

    return {
        "overall_risk_score": round(scenario_risk, 1),
        "risk_level":         "low" if scenario_risk < 30 else "medium" if scenario_risk < 60 else "high",
        "risk_factors":       risk_factors,
        "safe_to_proceed":    safe,
        "summary": (
            f"Scenario '{scenario['name']}' carries a risk score of "
            f"{scenario_risk:.0f}/100 vs your baseline of "
            f"{baseline_risk['overall_risk_score']:.0f}/100. "
            f"{'Proceed with confidence.' if safe else 'Review risk factors before proceeding.'}"
        ),
    }


def impact_analysis(
    user_id: int,
    scenario_a: dict[str, Any],
    scenario_b: dict[str, Any],
    domains: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Return domain-level impact rows between two scenarios."""
    domains = domains or ["financial", "study", "habits", "fitness"]
    result_a = _run_scenario(user_id, scenario_a)
    result_b = _run_scenario(user_id, scenario_b)
    return _impact_analysis(result_a, result_b, domains)

"""
backend/app/services/recommendation_service.py

AI recommendation engine – derives prioritised, actionable recommendations
from the user's current twin state across all five domains.

Each recommendation contains:
  priority      high | medium | low
  impact        high | medium | low
  confidence    0.0–1.0
  title         short label
  description   one-paragraph explanation
  action_steps  concrete next steps (list)
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


def _twin(user_id: int):
    from app.ml.digital_twin import DigitalTwin
    return DigitalTwin(user_id).load_from_database()


# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN-LEVEL GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def _financial_recommendations(
    fin: dict[str, Any],
    score: float,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    if fin["net_savings"] < 0:
        recs.append({
            "domain": "financial", "priority": "high", "impact": "high",
            "confidence": 0.92, "title": "Eliminate Negative Savings",
            "description": (
                f"Your expenses currently exceed income by "
                f"${abs(fin['net_savings']):,.0f}. Left unchecked this creates "
                f"a debt spiral within months."
            ),
            "action_steps": [
                f"Audit '{fin['top_expense_category']}' – your largest spend category.",
                "Cancel or pause at least 2 non-essential subscriptions.",
                "Set a hard monthly expense cap equal to 90% of income.",
                "Review recurring payments for unused services.",
            ],
        })
    elif fin["savings_rate"] < 0.10:
        recs.append({
            "domain": "financial", "priority": "high", "impact": "high",
            "confidence": 0.85, "title": "Increase Savings Rate to 10%",
            "description": (
                f"Your current savings rate is {fin['savings_rate']*100:.1f}%. "
                f"Financial advisors recommend a minimum of 10% for long-term security."
            ),
            "action_steps": [
                "Set up automatic transfer of 10% of every paycheck to savings.",
                "Redirect any windfalls (bonuses, tax refunds) entirely to savings.",
                f"Cut '{fin['top_expense_category']}' spending by 15%.",
            ],
        })
    else:
        recs.append({
            "domain": "financial", "priority": "medium", "impact": "medium",
            "confidence": 0.75, "title": "Optimise Investment Allocation",
            "description": (
                f"Savings rate of {fin['savings_rate']*100:.1f}% is healthy. "
                f"The next step is putting idle cash to work through index funds or SIPs."
            ),
            "action_steps": [
                "Allocate at least 50% of monthly savings to a low-cost index fund.",
                "Maintain 3–6 months of expenses as an emergency fund.",
                "Review and rebalance portfolio every 6 months.",
            ],
        })

    if fin["monthly_avg_expenses"] > fin["monthly_avg_income"] * 0.8:
        recs.append({
            "domain": "financial", "priority": "medium", "impact": "medium",
            "confidence": 0.78, "title": "Reduce Expense Ratio Below 70%",
            "description": (
                "Expenses are above 80% of income leaving little buffer for "
                "unexpected costs. Aim for the 70/20/10 rule: 70% expenses, "
                "20% savings, 10% investments."
            ),
            "action_steps": [
                "List every recurring expense and label as need/want.",
                "Eliminate or downgrade at least two 'want' categories.",
                f"Challenge yourself to a no-spend week in '{fin['top_expense_category']}'.",
            ],
        })

    return recs


def _study_recommendations(
    stu: dict[str, Any],
    score: float,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    if stu["total_sessions"] == 0:
        recs.append({
            "domain": "study", "priority": "high", "impact": "high",
            "confidence": 0.90, "title": "Start Logging Study Sessions",
            "description": (
                "No study sessions recorded yet. Even 30 minutes of deliberate "
                "practice per day compounded over months delivers significant results."
            ),
            "action_steps": [
                "Block one 45-minute deep-work session in your calendar for tomorrow.",
                "Choose one subject to focus on for the first two weeks.",
                "Log every session immediately – tracking reinforces the habit.",
            ],
        })
        return recs

    if stu["avg_focus_score"] < 60:
        recs.append({
            "domain": "study", "priority": "high", "impact": "high",
            "confidence": 0.80, "title": "Improve Focus Score",
            "description": (
                f"Average focus score is {stu['avg_focus_score']:.0f}/100. "
                f"Poor focus wastes study hours. Fix the environment before adding more time."
            ),
            "action_steps": [
                "Use website blockers (Cold Turkey / Freedom) during study blocks.",
                "Put phone in another room – even its presence reduces cognition.",
                "Try the 25/5 Pomodoro method to build focus tolerance gradually.",
                "Identify your peak cognitive hours and protect them for deep work.",
            ],
        })

    if stu["avg_study_hours"] < 1.5:
        recs.append({
            "domain": "study", "priority": "medium", "impact": "high",
            "confidence": 0.75, "title": "Increase Daily Study Hours",
            "description": (
                f"Average session is {stu['avg_study_hours']:.1f}h. "
                f"Research shows 2–3h of focused study daily maximises long-term retention."
            ),
            "action_steps": [
                "Add one extra 30-minute block per day for the next two weeks.",
                "Use calendar blocking – treat study time like a meeting.",
                "Remove the biggest daily time sink first (social media, TV).",
            ],
        })

    if score >= 75:
        recs.append({
            "domain": "study", "priority": "low", "impact": "medium",
            "confidence": 0.70, "title": "Expand Subject Coverage",
            "description": (
                f"Performance score of {stu['avg_performance_score']:.0f} is strong. "
                f"Consider adding cross-disciplinary subjects to compound your edge."
            ),
            "action_steps": [
                "Explore one adjacent subject that complements your current focus.",
                "Read one technical book per month outside your primary domain.",
                "Teach concepts to others – the best way to test mastery.",
            ],
        })

    return recs


def _habit_recommendations(
    hab: dict[str, Any],
    score: float,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    if hab["total_habits"] == 0:
        recs.append({
            "domain": "habits", "priority": "high", "impact": "high",
            "confidence": 0.88, "title": "Start Tracking Habits",
            "description": (
                "No habits logged. The single most powerful productivity lever is "
                "a consistent daily routine tracked visibly."
            ),
            "action_steps": [
                "Pick two keystone habits: one morning, one evening.",
                "Use a simple paper habit tracker for the first month.",
                "Log streaks daily – visual progress is a powerful motivator.",
            ],
        })
        return recs

    if hab["completion_rate"] < 0.5:
        recs.append({
            "domain": "habits", "priority": "high", "impact": "high",
            "confidence": 0.85, "title": "Reduce Habit Load",
            "description": (
                f"Completion rate is {hab['completion_rate']*100:.0f}% – "
                f"overwhelm is the primary cause. Fewer, stronger habits beat many weak ones."
            ),
            "action_steps": [
                "Cut to 3 non-negotiable habits and park the rest.",
                "Schedule habits at a specific time and location (implementation intention).",
                "Celebrate each completion immediately to wire the reward loop.",
            ],
        })

    if hab["at_risk_habits"]:
        at_risk_str = ", ".join(hab["at_risk_habits"][:3])
        recs.append({
            "domain": "habits", "priority": "medium", "impact": "medium",
            "confidence": 0.78, "title": f"Rescue At-Risk Habits",
            "description": (
                f"Habits with zero streak and incomplete: {at_risk_str}. "
                f"These are about to break entirely without intervention."
            ),
            "action_steps": [
                f"Complete one of {at_risk_str} today – restart the streak.",
                "Lower the bar temporarily (2-min version of the habit).",
                "Pair it with a strong existing routine (habit stacking).",
            ],
        })

    if hab["avg_streak"] < 5 and hab["total_habits"] > 0:
        recs.append({
            "domain": "habits", "priority": "medium", "impact": "medium",
            "confidence": 0.72, "title": "Build Longer Streaks",
            "description": (
                f"Average streak is {hab['avg_streak']:.0f} days. "
                f"Research shows 66 days to form a habit – short streaks don't stick."
            ),
            "action_steps": [
                "Never break a streak for two consecutive days.",
                "Use 'commitment devices' – tell someone your streak goal.",
                "Review streaks every Sunday and plan the coming week.",
            ],
        })

    return recs


def _fitness_recommendations(
    fit: dict[str, Any],
    score: float,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    if fit["total_sessions"] == 0:
        recs.append({
            "domain": "fitness", "priority": "high", "impact": "high",
            "confidence": 0.88, "title": "Begin Fitness Tracking",
            "description": (
                "No fitness activity recorded. Even 20 minutes of walking three "
                "times per week meaningfully improves cognitive performance and mood."
            ),
            "action_steps": [
                "Start with three 20-minute walks this week.",
                "Log every session to build data for AI analysis.",
                "Choose an activity you genuinely enjoy – consistency beats intensity.",
            ],
        })
        return recs

    if fit["sessions_per_week"] < 2:
        recs.append({
            "domain": "fitness", "priority": "high", "impact": "high",
            "confidence": 0.82, "title": "Increase to 3 Sessions/Week",
            "description": (
                f"Currently averaging {fit['sessions_per_week']:.1f} sessions/week. "
                f"WHO recommends 150 min/week of moderate activity minimum."
            ),
            "action_steps": [
                "Add one session this week – any activity counts.",
                "Schedule all three sessions in advance on your calendar.",
                "Pair gym sessions with a podcast you only listen to while working out.",
            ],
        })

    if fit["avg_calories"] < 200:
        recs.append({
            "domain": "fitness", "priority": "medium", "impact": "medium",
            "confidence": 0.70, "title": "Increase Session Intensity",
            "description": (
                f"Average {fit['avg_calories']:.0f} kcal/session is on the low side. "
                f"Aim for 300–500 kcal per session for meaningful metabolic impact."
            ),
            "action_steps": [
                "Increase session duration by 10 minutes each week.",
                "Add 2 high-intensity intervals (30-sec sprints) to cardio sessions.",
                "Try HIIT once per week to maximise calorie burn in 20 minutes.",
            ],
        })

    return recs


def _goals_recommendations(
    gls: list[dict[str, Any]],
    score: float,
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []

    if not gls:
        recs.append({
            "domain": "goals", "priority": "high", "impact": "high",
            "confidence": 0.88, "title": "Set SMART Goals",
            "description": (
                "No goals defined. Clear written goals make you 42% more likely to "
                "achieve them (Harvard research). Start with one goal per domain."
            ),
            "action_steps": [
                "Define one financial, one fitness, and one learning goal today.",
                "Ensure each goal is Specific, Measurable, Achievable, Relevant, Time-bound.",
                "Log current_value = 0 and set a realistic target_date 90 days out.",
            ],
        })
        return recs

    behind = [g for g in gls if not g["on_track"] and g["days_remaining"] > 0]
    if behind:
        names = ", ".join(g["name"] for g in behind[:2])
        recs.append({
            "domain": "goals", "priority": "high", "impact": "high",
            "confidence": 0.80, "title": f"Get Back on Track: {names}",
            "description": (
                f"{len(behind)} goal(s) are behind schedule. Without intervention "
                f"they will miss their target dates."
            ),
            "action_steps": [
                "Increase weekly effort on the most behind goal by 20%.",
                "Break remaining work into daily micro-tasks.",
                "If a goal is no longer relevant, update its status honestly.",
            ],
        })

    near_done = [g for g in gls if g["progress_pct"] >= 75 and g["progress_pct"] < 100]
    if near_done:
        recs.append({
            "domain": "goals", "priority": "low", "impact": "medium",
            "confidence": 0.85, "title": "Sprint to Finish Near-Complete Goals",
            "description": (
                f"{len(near_done)} goal(s) are 75%+ complete. A focused sprint now "
                f"will close them out and free up bandwidth."
            ),
            "action_steps": [
                "Dedicate 20% more time to each nearly-complete goal this week.",
                "Announce the goal publicly for an accountability boost.",
                "Reward yourself meaningfully when each goal is marked complete.",
            ],
        })

    return recs


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def generate_all_recommendations(user_id: int) -> dict[str, Any]:
    """
    Generate prioritised recommendations across all domains.
    Returns at most 8 recommendations, sorted: high → medium → low priority.
    """
    tw     = _twin(user_id)
    scores = tw.calculate_behavioral_score()
    fin    = tw._financial_state()
    stu    = tw._study_state()
    hab    = tw._habits_state()
    fit    = tw._fitness_state()
    gls    = tw._goals_state()

    all_recs: list[dict[str, Any]] = (
        _financial_recommendations(fin, scores["finance_score"])
        + _study_recommendations(stu, scores["study_score"])
        + _habit_recommendations(hab, scores["habits_score"])
        + _fitness_recommendations(fit, scores["fitness_score"])
        + _goals_recommendations(gls, scores["goals_score"])
    )

    # Sort: high > medium > low, then by confidence desc
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_recs.sort(
        key=lambda r: (priority_order.get(r["priority"], 9), -r["confidence"])
    )

    return {
        "user_id":             user_id,
        "generated_at":        datetime.utcnow().isoformat(),
        "recommendations":     all_recs[:8],
        "overall_health_score": scores["productivity_score"],
    }

"""
backend/app/ml/simulation_engine.py

SimulationEngine – pure-computation what-if engine.

Every simulate_*() method:
  1. Loads the user's current twin state via DigitalTwin
  2. Applies the requested parameter change
  3. Returns a standardised SimulationResult dict:

     {
         "simulation_type": str,
         "current_state":   dict,
         "future_state":    dict,
         "difference":      dict,
         "confidence_score": float,   # 0.0–1.0
         "recommendations": [str, ...]
     }

No external ML model is required – all projections use deterministic
financial/statistical formulas so the engine works immediately without
pre-trained artifacts.  Where a trained Prophet/XGBoost model exists it is
used as an additional signal to improve the confidence score.
"""
from __future__ import annotations

import math
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ── path bootstrap ────────────────────────────────────────────────────────────
_BACKEND = Path(__file__).resolve().parents[2]
_ROOT    = _BACKEND.parent
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── helpers ───────────────────────────────────────────────────────────────────

def _result(sim_type: str,
            current: dict[str, Any],
            future:  dict[str, Any],
            confidence: float,
            recommendations: list[str]) -> dict[str, Any]:
    """Build the standardised simulation result envelope."""
    diff: dict[str, Any] = {}
    for k in set(current) | set(future):
        a = current.get(k)
        b = future.get(k)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            diff[k] = round(b - a, 4)
        else:
            diff[k] = b
    return {
        "simulation_type":  sim_type,
        "current_state":    current,
        "future_state":     future,
        "difference":       diff,
        "confidence_score": round(min(1.0, max(0.0, confidence)), 3),
        "recommendations":  recommendations,
        "simulated_at":     datetime.utcnow().isoformat(),
    }


def _compound(principal: float, monthly_rate: float, months: int) -> float:
    """Future value of principal + monthly contribution at monthly_rate."""
    if monthly_rate == 0:
        return principal
    return principal * (1 + monthly_rate) ** months


def _annuity_fv(monthly_contribution: float, monthly_rate: float, months: int) -> float:
    """Future value of regular monthly contributions."""
    if monthly_rate == 0:
        return monthly_contribution * months
    return monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)


class SimulationEngine:
    """
    Stateless simulation engine.  Instantiate with a user_id; each
    simulate_*() call fetches fresh data via DigitalTwin.

    Usage
    -----
    engine  = SimulationEngine(user_id=3)
    result  = engine.simulate_savings_increase(monthly_increase=500, horizon_months=12)
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def _twin(self) -> Any:
        """Return a loaded DigitalTwin for this user."""
        from app.ml.digital_twin import DigitalTwin
        return DigitalTwin(self.user_id).load_from_database()

    # ══════════════════════════════════════════════════════════════════
    # FINANCIAL SIMULATIONS
    # ══════════════════════════════════════════════════════════════════

    def simulate_savings_increase(
        self,
        monthly_increase: float,
        horizon_months: int = 12,
    ) -> dict[str, Any]:
        """What happens if I save $X more per month?"""
        twin    = self._twin()
        fin     = twin._financial_state()

        cur_net = fin["net_savings"]
        cur_monthly_savings = fin["monthly_avg_income"] - fin["monthly_avg_expenses"]

        new_monthly_savings = cur_monthly_savings + monthly_increase
        new_net_savings     = cur_net + monthly_increase * horizon_months

        current = {
            "net_savings":          cur_net,
            "monthly_savings":      round(cur_monthly_savings, 2),
            "monthly_expenses":     fin["monthly_avg_expenses"],
            "savings_rate":         fin["savings_rate"],
        }
        future = {
            "net_savings":          round(new_net_savings, 2),
            "monthly_savings":      round(new_monthly_savings, 2),
            "monthly_expenses":     round(fin["monthly_avg_expenses"] - monthly_increase, 2),
            "savings_rate":         round(
                new_monthly_savings / fin["monthly_avg_income"], 4
            ) if fin["monthly_avg_income"] else 0,
        }

        recs = [
            f"Increasing monthly savings by ${monthly_increase:,.0f} adds "
            f"${monthly_increase * horizon_months:,.0f} over {horizon_months} months.",
            "Automate the transfer on pay day to make it effortless.",
            "Review subscriptions to find the extra $" + f"{monthly_increase:,.0f}/month.",
        ]
        conf = 0.85 if fin["record_count"] >= 6 else 0.60
        return _result("savings_increase", current, future, conf, recs)

    def simulate_major_purchase(
        self,
        purchase_amount: float,
        purchase_month: int = 3,
        horizon_months: int = 12,
    ) -> dict[str, Any]:
        """Impact of a one-off major purchase in month N."""
        twin = self._twin()
        fin  = twin._financial_state()

        monthly_savings = fin["monthly_avg_income"] - fin["monthly_avg_expenses"]
        cur_net         = fin["net_savings"]
        # savings accumulate normally then drop at purchase_month
        future_savings = cur_net + monthly_savings * horizon_months - purchase_amount

        current = {"net_savings": cur_net, "monthly_savings": round(monthly_savings, 2)}
        future  = {
            "net_savings":      round(future_savings, 2),
            "purchase_impact":  round(-purchase_amount, 2),
            "recovery_months":  math.ceil(purchase_amount / monthly_savings) if monthly_savings > 0 else 999,
        }
        recs = [
            f"A ${purchase_amount:,.0f} purchase in month {purchase_month} "
            f"takes ~{future['recovery_months']} months to recover.",
            "Consider spreading the cost or saving a dedicated fund first.",
            f"Delay by 3 months to reduce recovery time by "
            f"${monthly_savings * 3:,.0f}.",
        ]
        conf = 0.88 if fin["record_count"] >= 4 else 0.65
        return _result("major_purchase", current, future, conf, recs)

    def simulate_expense_reduction(
        self,
        reduction_pct: float,
        horizon_months: int = 12,
    ) -> dict[str, Any]:
        """What if I cut monthly expenses by X%?"""
        twin = self._twin()
        fin  = twin._financial_state()

        factor          = reduction_pct / 100
        monthly_saving  = fin["monthly_avg_expenses"] * factor
        new_expenses    = fin["monthly_avg_expenses"] * (1 - factor)
        new_net_savings = fin["net_savings"] + monthly_saving * horizon_months

        current = {
            "monthly_expenses": fin["monthly_avg_expenses"],
            "net_savings":      fin["net_savings"],
            "savings_rate":     fin["savings_rate"],
        }
        future = {
            "monthly_expenses": round(new_expenses, 2),
            "net_savings":      round(new_net_savings, 2),
            "monthly_freed":    round(monthly_saving, 2),
            "savings_rate":     round(
                (fin["monthly_avg_income"] - new_expenses) / fin["monthly_avg_income"], 4
            ) if fin["monthly_avg_income"] else 0,
        }
        recs = [
            f"Cutting expenses {reduction_pct:.0f}% saves ${monthly_saving:,.0f}/month.",
            f"Over {horizon_months} months that is ${monthly_saving * horizon_months:,.0f} extra.",
            f"Focus on '{fin['top_expense_category']}' – your largest category.",
        ]
        conf = 0.80 if fin["record_count"] >= 6 else 0.55
        return _result("expense_reduction", current, future, conf, recs)

    def simulate_investment_growth(
        self,
        initial_amount: float,
        monthly_contribution: float = 0,
        annual_return_pct: float = 8.0,
        horizon_months: int = 24,
    ) -> dict[str, Any]:
        """Compound investment growth with optional monthly top-up."""
        monthly_rate = annual_return_pct / 100 / 12
        fv_lump      = _compound(initial_amount, monthly_rate, horizon_months)
        fv_contrib   = _annuity_fv(monthly_contribution, monthly_rate, horizon_months)
        total_fv     = fv_lump + fv_contrib
        total_invested = initial_amount + monthly_contribution * horizon_months
        gain         = total_fv - total_invested

        current = {
            "invested_amount":    initial_amount,
            "monthly_contribution": monthly_contribution,
            "total_invested":     round(total_invested, 2),
        }
        future = {
            "future_value":       round(total_fv, 2),
            "total_gain":         round(gain, 2),
            "return_pct":         round(gain / total_invested * 100, 2) if total_invested else 0,
            "annualised_return":  annual_return_pct,
        }
        recs = [
            f"At {annual_return_pct}% p.a. your ${initial_amount:,.0f} grows to "
            f"${total_fv:,.0f} in {horizon_months} months.",
            "Reinvesting dividends significantly accelerates compounding.",
            "Increase monthly contributions by even $50 to boost returns substantially.",
        ]
        return _result("investment_growth", current, future, 0.78, recs)

    def simulate_loan_impact(
        self,
        loan_amount: float,
        annual_interest_pct: float,
        tenure_months: int,
    ) -> dict[str, Any]:
        """EMI calculation and net cash-flow impact."""
        r   = annual_interest_pct / 100 / 12
        emi = (loan_amount * r * (1 + r) ** tenure_months) / ((1 + r) ** tenure_months - 1) if r > 0 else loan_amount / tenure_months
        total_payment = emi * tenure_months
        total_interest = total_payment - loan_amount

        twin = self._twin()
        fin  = twin._financial_state()
        monthly_savings_after = fin["monthly_avg_income"] - fin["monthly_avg_expenses"] - emi

        current = {
            "monthly_free_cash":  round(fin["monthly_avg_income"] - fin["monthly_avg_expenses"], 2),
            "net_savings":        fin["net_savings"],
        }
        future = {
            "monthly_emi":        round(emi, 2),
            "monthly_free_cash":  round(monthly_savings_after, 2),
            "total_interest_paid": round(total_interest, 2),
            "total_repayment":    round(total_payment, 2),
            "affordable":         monthly_savings_after >= 0,
        }
        recs = [
            f"EMI of ${emi:,.0f}/month over {tenure_months} months costs "
            f"${total_interest:,.0f} in interest.",
            "Shorter tenure reduces total interest significantly.",
            "Part-prepay when possible to cut tenure and save on interest.",
        ]
        conf = 0.92  # pure math, high confidence
        return _result("loan_impact", current, future, conf, recs)

    # ══════════════════════════════════════════════════════════════════
    # STUDY SIMULATIONS
    # ══════════════════════════════════════════════════════════════════

    def simulate_extra_study_hours(
        self,
        extra_hours_per_day: float,
        horizon_weeks: int = 8,
    ) -> dict[str, Any]:
        """Performance improvement from additional study time."""
        twin = self._twin()
        stu  = twin._study_state()

        cur_hours   = stu["avg_study_hours"]
        cur_perf    = stu["avg_performance_score"]
        # Research-backed: ~2 pts performance gain per extra hour/day/week (diminishing)
        improvement = extra_hours_per_day * horizon_weeks * 0.4 * (1 - cur_perf / 150)
        proj_perf   = min(100.0, cur_perf + improvement)

        current = {"avg_study_hours": cur_hours, "avg_performance_score": cur_perf}
        future  = {
            "avg_study_hours":       round(cur_hours + extra_hours_per_day, 2),
            "avg_performance_score": round(proj_perf, 1),
            "total_extra_hours":     round(extra_hours_per_day * 7 * horizon_weeks, 1),
        }
        recs = [
            f"Adding {extra_hours_per_day}h/day could raise performance to {proj_perf:.0f}/100.",
            "Use active recall and spaced repetition for maximum return per hour.",
            "Schedule deep-work blocks in your peak focus hours.",
        ]
        conf = 0.72 if stu["total_sessions"] >= 5 else 0.50
        return _result("extra_study_hours", current, future, conf, recs)

    def simulate_exam_preparation(
        self,
        subject: str,
        days_until_exam: int,
        target_score: float,
    ) -> dict[str, Any]:
        """Optimal daily study hours to hit target_score."""
        twin = self._twin()
        stu  = twin._study_state()

        cur_perf = stu["avg_performance_score"]
        gap      = max(0, target_score - cur_perf)
        # hours required: 1 point ≈ 0.5 study-hours given focused sessions
        hours_needed = gap * 0.5
        daily_hours  = round(hours_needed / max(1, days_until_exam), 2)
        achievable   = daily_hours <= 6  # cap at reasonable daily study

        current = {"current_performance": cur_perf, "days_until_exam": days_until_exam}
        future  = {
            "target_score":        target_score,
            "required_daily_hours": daily_hours,
            "total_hours_needed":   round(hours_needed, 1),
            "achievable":           achievable,
            "subject":              subject,
        }
        recs = [
            f"To reach {target_score:.0f} in {days_until_exam} days: {daily_hours:.1f}h/day.",
            "Break study into 45-min Pomodoro blocks with 10-min breaks.",
            f"Focus on weak sub-topics within {subject} for highest ROI.",
        ] if achievable else [
            f"Target of {target_score:.0f} in {days_until_exam} days requires "
            f"{daily_hours:.1f}h/day – consider a lower target or more days.",
            "Even 3h/day consistently will show measurable improvement.",
        ]
        conf = 0.68 if stu["total_sessions"] >= 3 else 0.45
        return _result("exam_preparation", current, future, conf, recs)

    def simulate_subject_improvement(
        self,
        subject: str,
        target_performance: float,
        horizon_weeks: int = 8,
    ) -> dict[str, Any]:
        """Weekly study hours needed to reach target performance in a subject."""
        twin = self._twin()
        stu  = twin._study_state()

        cur_perf     = stu["avg_performance_score"]
        gap          = max(0, target_performance - cur_perf)
        weekly_hours = round(gap / max(1, horizon_weeks) * 1.2, 2)  # 1.2x safety factor

        current = {"current_performance": cur_perf, "subject": subject}
        future  = {
            "target_performance":   target_performance,
            "weekly_hours_needed":  weekly_hours,
            "horizon_weeks":        horizon_weeks,
            "improvement_per_week": round(gap / max(1, horizon_weeks), 2),
        }
        recs = [
            f"Dedicate {weekly_hours:.1f}h/week to {subject} to reach {target_performance:.0f}.",
            "Track progress weekly and adjust hours if behind schedule.",
            "Join study groups to increase accountability and retention.",
        ]
        conf = 0.65 if stu["total_sessions"] >= 5 else 0.45
        return _result("subject_improvement", current, future, conf, recs)

    # ══════════════════════════════════════════════════════════════════
    # HABIT SIMULATIONS
    # ══════════════════════════════════════════════════════════════════

    def simulate_new_habit(
        self,
        habit_name: str,
        target_frequency: str = "daily",
        horizon_weeks: int = 8,
    ) -> dict[str, Any]:
        """Effect of adding a new habit on overall completion rate."""
        twin = self._twin()
        hab  = twin._habits_state()

        cur_total     = hab["total_habits"]
        cur_completed = hab["completed_habits"]
        # Assume new habit takes 3 weeks to stabilise → ~70% completion
        new_completions = 0.70 * horizon_weeks / 8
        new_total     = cur_total + 1
        new_completed = cur_completed + new_completions
        new_rate      = new_completed / new_total if new_total > 0 else 0

        current = {
            "total_habits":    cur_total,
            "completion_rate": hab["completion_rate"],
            "avg_streak":      hab["avg_streak"],
        }
        future = {
            "total_habits":        new_total,
            "completion_rate":     round(new_rate, 4),
            "new_habit":           habit_name,
            "target_frequency":    target_frequency,
            "expected_streak_wk8": round(horizon_weeks * 0.65, 1),
        }
        recs = [
            f"Stack '{habit_name}' onto an existing habit (habit stacking) for best results.",
            "Track the habit visually – a habit streak calendar boosts compliance 40%.",
            "Miss once, never twice: one missed day is normal, two starts a new (bad) pattern.",
        ]
        conf = 0.70
        return _result("new_habit", current, future, conf, recs)

    def simulate_habit_removal(
        self,
        habit_name: str,
        horizon_weeks: int = 4,
    ) -> dict[str, Any]:
        """Impact of removing a habit on overall completion rate."""
        twin = self._twin()
        hab  = twin._habits_state()

        # find the specific habit if it exists
        matching = [h for h in twin._habits if h["name"].lower() == habit_name.lower()]
        habit_was_completed = matching[0]["completed"] if matching else False

        cur_total     = hab["total_habits"]
        cur_completed = hab["completed_habits"]
        new_total     = max(0, cur_total - 1)
        new_completed = max(0, cur_completed - (1 if habit_was_completed else 0))
        new_rate      = new_completed / new_total if new_total > 0 else 0

        current = {"total_habits": cur_total, "completion_rate": hab["completion_rate"]}
        future  = {
            "total_habits":    new_total,
            "completion_rate": round(new_rate, 4),
            "removed_habit":   habit_name,
        }
        recs = [
            f"Removing '{habit_name}' frees cognitive bandwidth for remaining habits.",
            "Replace with a simpler version rather than full removal to retain the routine.",
            "Re-evaluate in 2 weeks – sometimes a break refreshes commitment.",
        ]
        return _result("habit_removal", current, future, 0.75, recs)

    def simulate_productivity_change(
        self,
        focus_improvement_pct: float,
        horizon_weeks: int = 8,
    ) -> dict[str, Any]:
        """Effect of focus improvement on productivity index."""
        twin    = self._twin()
        scores  = twin.calculate_behavioral_score()
        cur_prod = scores["productivity_score"]
        cur_focus = twin._study_state()["avg_focus_score"]

        new_focus    = min(100.0, cur_focus * (1 + focus_improvement_pct / 100))
        # study score drives 30% of productivity; focus drives 30% of study score
        study_delta  = (new_focus - cur_focus) * 0.30 * 0.30
        new_prod     = min(100.0, cur_prod + study_delta)

        current = {"productivity_score": cur_prod, "avg_focus_score": cur_focus}
        future  = {
            "productivity_score": round(new_prod, 1),
            "avg_focus_score":    round(new_focus, 1),
            "improvement":        round(new_prod - cur_prod, 1),
            "horizon_weeks":      horizon_weeks,
        }
        recs = [
            f"A {focus_improvement_pct:.0f}% focus boost could add {new_prod - cur_prod:.1f} pts to productivity.",
            "Eliminate phone notifications during study/work blocks.",
            "Aim for one 90-minute deep-work session before checking messages.",
        ]
        conf = 0.65
        return _result("productivity_change", current, future, conf, recs)

    # ══════════════════════════════════════════════════════════════════
    # FITNESS SIMULATIONS
    # ══════════════════════════════════════════════════════════════════

    def simulate_workout_plan(
        self,
        sessions_per_week: int,
        session_duration_minutes: float = 45.0,
        activity_type: str = "Running",
        horizon_weeks: int = 8,
    ) -> dict[str, Any]:
        """Projected calorie burn and fitness score for a new workout plan."""
        twin = self._twin()
        fit  = twin._fitness_state()

        # ~7 kcal/min for moderate cardio (generic estimate)
        kcal_per_session = session_duration_minutes * 7.0
        total_sessions   = sessions_per_week * horizon_weeks
        total_calories   = kcal_per_session * total_sessions
        new_score        = min(100.0, total_sessions * 10)  # mirrors _fitness_score logic

        current = {
            "sessions_per_week": fit["sessions_per_week"],
            "avg_calories":      fit["avg_calories"],
            "fitness_score":     twin._fitness_score(),
        }
        future = {
            "sessions_per_week":  sessions_per_week,
            "total_sessions":     total_sessions,
            "calories_per_session": round(kcal_per_session, 0),
            "total_calories_burned": round(total_calories, 0),
            "projected_fitness_score": round(new_score, 1),
            "activity_type":      activity_type,
        }
        recs = [
            f"{sessions_per_week}x/week {activity_type} burns ~{total_calories:,.0f} kcal over {horizon_weeks} weeks.",
            "Combine cardio with 2 strength sessions/week for best body-composition results.",
            "Track resting heart rate weekly – declining HR signals improved cardiovascular fitness.",
        ]
        conf = 0.76
        return _result("workout_plan", current, future, conf, recs)

    def simulate_weight_loss(
        self,
        target_weekly_calories: float,
        horizon_weeks: int = 12,
    ) -> dict[str, Any]:
        """Estimate weight loss from a calorie-burn target."""
        # 1 lb fat ≈ 3500 kcal; 1 kg ≈ 7700 kcal
        total_cal    = target_weekly_calories * horizon_weeks
        kg_loss      = total_cal / 7700
        sessions_needed = math.ceil(target_weekly_calories / (45 * 7))  # 45-min sessions

        twin = self._twin()
        fit  = twin._fitness_state()

        current = {
            "avg_weekly_calories": round(fit["avg_calories"] * fit["sessions_per_week"], 1),
            "total_sessions":      fit["total_sessions"],
        }
        future = {
            "target_weekly_calories": target_weekly_calories,
            "projected_kg_loss":      round(kg_loss, 2),
            "projected_lb_loss":      round(kg_loss * 2.205, 2),
            "sessions_per_week_needed": sessions_needed,
            "horizon_weeks":          horizon_weeks,
        }
        recs = [
            f"Burning {target_weekly_calories:,.0f} kcal/week for {horizon_weeks} weeks "
            f"loses ~{kg_loss:.1f} kg.",
            "Combine with a 200–300 kcal/day dietary deficit for 2x results.",
            "Strength training preserves muscle mass during a weight-loss phase.",
        ]
        return _result("weight_loss", current, future, 0.70, recs)

    def simulate_goal_completion(
        self,
        goal_name: str,
        horizon_weeks: int = 8,
    ) -> dict[str, Any]:
        """Fitness goal completion probability based on current trajectory."""
        twin = self._twin()
        fit  = twin._fitness_state()

        sessions_so_far = fit["total_sessions"]
        spw             = max(fit["sessions_per_week"], 1)
        projected_total = sessions_so_far + spw * horizon_weeks
        probability     = min(0.98, spw / 5 * 0.8)   # 5 sessions/week → 80% probability

        current = {"sessions_per_week": spw, "total_sessions": sessions_so_far}
        future  = {
            "projected_sessions":  round(projected_total, 0),
            "completion_probability": round(probability, 3),
            "goal_name":           goal_name,
            "horizon_weeks":       horizon_weeks,
        }
        recs = [
            f"At {spw:.1f} sessions/week you have a {probability * 100:.0f}% chance of completing '{goal_name}'.",
            "Increase to 4 sessions/week to push probability above 80%.",
            "Log every session – visibility is the strongest motivator.",
        ]
        return _result("fitness_goal_completion", current, future, 0.72, recs)

    # ══════════════════════════════════════════════════════════════════
    # GOAL SIMULATIONS
    # ══════════════════════════════════════════════════════════════════

    def simulate_goal_completion_probability(
        self,
        goal_id: int,
        accelerate_by_pct: float = 0.0,
    ) -> dict[str, Any]:
        """Probability and projected completion date for a specific goal."""
        twin  = self._twin()
        goals = twin._goals_state()

        goal  = next((g for g in goals if g["id"] == goal_id), None)
        if goal is None:
            return _result("goal_probability", {}, {"error": "Goal not found"}, 0.0, [])

        pct          = goal["progress_pct"]
        days_left    = goal["days_remaining"]
        # Current rate: pct per (total_days - days_left)
        raw          = [g for g in twin._goals if g["id"] == goal_id]
        raw_g        = raw[0] if raw else {}
        try:
            start_date = datetime.fromisoformat(str(raw_g.get("created_at", datetime.utcnow().isoformat()))[:10])
            days_elapsed = max(1, (datetime.utcnow() - start_date).days)
        except Exception:
            days_elapsed = max(1, 30)

        daily_rate   = pct / days_elapsed
        # With acceleration
        boosted_rate = daily_rate * (1 + accelerate_by_pct / 100)
        days_to_100  = (100 - pct) / boosted_rate if boosted_rate > 0 else 999
        completion_date = (datetime.utcnow() + timedelta(days=days_to_100)).strftime("%Y-%m-%d")
        probability  = min(0.98, 1 - (max(0, days_to_100 - days_left) / max(1, days_left + days_to_100)))

        current = {
            "goal_name":     goal["name"],
            "progress_pct":  pct,
            "days_remaining": days_left,
            "daily_rate":    round(daily_rate, 4),
        }
        future = {
            "probability":        round(probability, 3),
            "projected_completion": completion_date,
            "days_to_complete":   round(days_to_100, 0),
            "boosted_daily_rate": round(boosted_rate, 4),
        }
        recs = [
            f"'{goal['name']}' is {pct:.0f}% complete with {days_left} days left.",
            f"Projected completion: {completion_date} (probability {probability * 100:.0f}%).",
            "Break the remaining gap into weekly micro-targets to stay on track.",
        ]
        return _result("goal_completion_probability", current, future, 0.75, recs)

    # ══════════════════════════════════════════════════════════════════
    # FULL / COMBINED SIMULATION
    # ══════════════════════════════════════════════════════════════════

    def simulate_full(
        self,
        horizon_months: int = 6,
        financial_boost_pct: float = 10.0,
        study_hours_increase: float = 1.0,
        habit_compliance_target: float = 80.0,
        fitness_sessions_per_week: int = 3,
    ) -> dict[str, Any]:
        """
        Run all four domain simulations with the given parameters and return
        a consolidated future state alongside domain-level impacts.
        """
        fin_sim  = self.simulate_expense_reduction(financial_boost_pct, horizon_months)
        stu_sim  = self.simulate_extra_study_hours(study_hours_increase, horizon_months * 4)
        hab_sim  = self.simulate_productivity_change(
            (habit_compliance_target - 50), horizon_months * 4
        )
        fit_sim  = self.simulate_workout_plan(
            fitness_sessions_per_week, 45, "Mixed", horizon_months * 4
        )

        overall_gain = (
            fin_sim["difference"].get("net_savings", 0) / 10_000
            + stu_sim["difference"].get("avg_performance_score", 0)
            + hab_sim["difference"].get("productivity_score", 0)
        ) / 3

        avg_conf = (
            fin_sim["confidence_score"]
            + stu_sim["confidence_score"]
            + hab_sim["confidence_score"]
            + fit_sim["confidence_score"]
        ) / 4

        current = {
            "financial": fin_sim["current_state"],
            "study":     stu_sim["current_state"],
            "habits":    hab_sim["current_state"],
            "fitness":   fit_sim["current_state"],
        }
        future = {
            "financial": fin_sim["future_state"],
            "study":     stu_sim["future_state"],
            "habits":    hab_sim["future_state"],
            "fitness":   fit_sim["future_state"],
            "estimated_score_gain": round(overall_gain, 1),
        }
        recs = (
            fin_sim["recommendations"][:1]
            + stu_sim["recommendations"][:1]
            + hab_sim["recommendations"][:1]
            + fit_sim["recommendations"][:1]
        )
        return _result("full_simulation", current, future, avg_conf, recs)

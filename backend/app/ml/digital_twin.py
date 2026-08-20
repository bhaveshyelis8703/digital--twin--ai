"""
backend/app/ml/digital_twin.py

DigitalTwin – builds a unified, queryable representation of a user's state
across all five life domains (financial, study, habits, fitness, goals) and
exposes projection, scoring and snapshot utilities.

All DB access goes through SessionLocal (not injected sessions) so this class
can be called from any context – services, background tasks or tests.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ── path bootstrap (mirrors forecasting_service.py pattern) ──────────────────
_BACKEND = Path(__file__).resolve().parents[2]   # backend/
_ROOT    = _BACKEND.parent                       # project root
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


class DigitalTwin:
    """
    Virtual representation of a single user.

    Usage
    -----
    twin = DigitalTwin(user_id=3)
    twin.load_from_database()
    state  = twin.build_current_state()
    scores = twin.calculate_behavioral_score()
    snap   = twin.save_snapshot("baseline")
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, user_id: int) -> None:
        self.user_id   = user_id
        self._financial: list[dict] = []
        self._study:     list[dict] = []
        self._habits:    list[dict] = []
        self._fitness:   list[dict] = []
        self._goals:     list[dict] = []
        self._loaded     = False

    # ------------------------------------------------------------------
    # 1. load_from_database
    # ------------------------------------------------------------------

    def load_from_database(self) -> "DigitalTwin":
        """Pull every domain's raw rows from the DB and cache them."""
        from app.core.database import SessionLocal
        from app.models.user import (
            FinancialRecord, FitnessActivity, Goal, Habit, StudyActivity,
        )

        db = SessionLocal()
        try:
            fin = db.query(FinancialRecord).filter(
                FinancialRecord.user_id == self.user_id
            ).all()
            self._financial = [
                {
                    "id": r.id, "record_type": r.record_type,
                    "amount": r.amount, "date": r.date.isoformat(),
                    "category": r.category,
                    "recurring_frequency": r.recurring_frequency,
                    "goal_impact": r.goal_impact,
                }
                for r in fin
            ]

            stu = db.query(StudyActivity).filter(
                StudyActivity.user_id == self.user_id
            ).all()
            self._study = [
                {
                    "id": r.id, "subject": r.subject,
                    "study_date": r.study_date.isoformat(),
                    "study_hours": r.study_hours,
                    "focus_score": r.focus_score,
                    "task_completion": r.task_completion,
                    "performance_score": r.performance_score,
                }
                for r in stu
            ]

            hab = db.query(Habit).filter(Habit.user_id == self.user_id).all()
            self._habits = [
                {
                    "id": r.id, "name": r.name,
                    "target_frequency": r.target_frequency,
                    "completed": r.completed, "streak": r.streak,
                }
                for r in hab
            ]

            fit = db.query(FitnessActivity).filter(
                FitnessActivity.user_id == self.user_id
            ).all()
            self._fitness = [
                {
                    "id": r.id, "activity_type": r.activity_type,
                    "duration": r.duration,
                    "calories_burned": r.calories_burned,
                    "activity_date": r.activity_date.isoformat(),
                }
                for r in fit
            ]

            gls = db.query(Goal).filter(Goal.user_id == self.user_id).all()
            self._goals = [
                {
                    "id": r.id, "name": r.name, "description": r.description,
                    "target_value": r.target_value,
                    "current_value": r.current_value,
                    "target_date": r.target_date.isoformat(),
                    "status": r.status,
                }
                for r in gls
            ]
        finally:
            db.close()

        self._loaded = True
        return self

    # ------------------------------------------------------------------
    # 2. build_current_state
    # ------------------------------------------------------------------

    def build_current_state(self) -> dict[str, Any]:
        """
        Aggregate raw rows into a unified state dict with the structure:

            {
                "financial": {...},
                "study": {...},
                "habits": {...},
                "fitness": {...},
                "goals": [...],
                "productivity_score": float,
                "risk_score": float,
                "behavioral_patterns": {...},
            }
        """
        if not self._loaded:
            self.load_from_database()

        return {
            "user_id": self.user_id,
            "snapshot_at": datetime.utcnow().isoformat(),
            "financial": self._financial_state(),
            "study":     self._study_state(),
            "habits":    self._habits_state(),
            "fitness":   self._fitness_state(),
            "goals":     self._goals_state(),
            "productivity_score": self.calculate_behavioral_score()["productivity_score"],
            "risk_score":         self.calculate_risk_score(),
            "behavioral_patterns": self._behavioral_patterns(),
        }

    # ------------------------------------------------------------------
    # 3. project_state   (simple forward projection)
    # ------------------------------------------------------------------

    def project_state(self, horizon_months: int = 6) -> dict[str, Any]:
        """
        Extrapolate each domain forward by *horizon_months* using linear
        trend estimates derived from existing data.  Returns the same
        structure as build_current_state() but with projected values.
        """
        if not self._loaded:
            self.load_from_database()

        current = self.build_current_state()

        # ── financial projection ─────────────────────────────────────
        fin     = current["financial"]
        monthly = fin.get("monthly_avg_income", 0) - fin.get("monthly_avg_expenses", 0)
        proj_fin = dict(fin)
        proj_fin["net_savings"] = fin.get("net_savings", 0) + monthly * horizon_months
        proj_fin["projected_months"] = horizon_months

        # ── study projection ─────────────────────────────────────────
        stu      = current["study"]
        perf_now = stu.get("avg_performance_score", 0)
        # modest improvement: +1 pt/month if already studying
        perf_proj = min(100.0, perf_now + horizon_months * (1.0 if perf_now > 0 else 0))
        proj_stu = dict(stu)
        proj_stu["projected_performance"] = perf_proj

        # ── habits projection ────────────────────────────────────────
        hab      = current["habits"]
        comp_now = hab.get("completion_rate", 0)
        # streaks compound: each month adds 2% up to 95%
        comp_proj = min(0.95, comp_now + horizon_months * 0.02)
        proj_hab = dict(hab)
        proj_hab["projected_completion_rate"] = comp_proj

        # ── fitness projection ───────────────────────────────────────
        fit      = current["fitness"]
        cal_now  = fit.get("avg_calories", 0)
        proj_fit = dict(fit)
        proj_fit["projected_total_calories"] = cal_now * (fit.get("sessions_per_week", 0) or 1) * 4 * horizon_months

        # ── goals projection ─────────────────────────────────────────
        proj_goals = []
        for g in current["goals"]:
            pg = dict(g)
            pct = g.get("progress_pct", 0)
            # linear: same monthly rate continues
            monthly_rate = pct / max(1, (horizon_months * 4))
            pg["projected_progress_pct"] = min(100.0, pct + monthly_rate * horizon_months * 4)
            pg["likely_completion"] = pg["projected_progress_pct"] >= 100
            proj_goals.append(pg)

        return {
            "user_id": self.user_id,
            "horizon_months": horizon_months,
            "projected_at": datetime.utcnow().isoformat(),
            "financial": proj_fin,
            "study":     proj_stu,
            "habits":    proj_hab,
            "fitness":   proj_fit,
            "goals":     proj_goals,
        }

    # ------------------------------------------------------------------
    # 4. calculate_behavioral_score
    # ------------------------------------------------------------------

    def calculate_behavioral_score(self) -> dict[str, float]:
        """
        Returns a dict of domain scores (0-100) plus a weighted
        productivity_score.

        Weights:
            study    30 %
            habits   25 %
            fitness  20 %
            finance  15 %
            goals    10 %
        """
        if not self._loaded:
            self.load_from_database()

        study_score   = self._study_score()
        habits_score  = self._habits_score()
        fitness_score = self._fitness_score()
        finance_score = self._finance_score()
        goals_score   = self._goals_score()

        productivity = (
            study_score   * 0.30
            + habits_score  * 0.25
            + fitness_score * 0.20
            + finance_score * 0.15
            + goals_score   * 0.10
        )

        return {
            "study_score":    round(study_score, 1),
            "habits_score":   round(habits_score, 1),
            "fitness_score":  round(fitness_score, 1),
            "finance_score":  round(finance_score, 1),
            "goals_score":    round(goals_score, 1),
            "productivity_score": round(productivity, 1),
        }

    # ------------------------------------------------------------------
    # 5. calculate_risk_score
    # ------------------------------------------------------------------

    def calculate_risk_score(self) -> float:
        """
        0 = no risk, 100 = maximum risk.
        Derived from: negative savings, low habit completion,
        low fitness, missed goals.
        """
        if not self._loaded:
            self.load_from_database()

        risk = 0.0

        # financial risk
        fin = self._financial_state()
        if fin["net_savings"] < 0:
            risk += 25
        elif fin["savings_rate"] < 0.05:
            risk += 10

        # habit risk
        hab = self._habits_state()
        if hab["completion_rate"] < 0.4:
            risk += 20
        elif hab["completion_rate"] < 0.6:
            risk += 10

        # fitness risk
        fit = self._fitness_state()
        if fit["sessions_per_week"] < 1:
            risk += 20
        elif fit["sessions_per_week"] < 2:
            risk += 10

        # goals risk
        gls = self._goals_state()
        overdue = sum(1 for g in gls if not g["on_track"])
        risk += min(25, overdue * 8)

        # study risk
        stu = self._study_state()
        if stu["avg_performance_score"] < 50:
            risk += 10

        return round(min(risk, 100), 1)

    # ------------------------------------------------------------------
    # 6. generate_summary
    # ------------------------------------------------------------------

    def generate_summary(self) -> dict[str, Any]:
        """Lightweight summary dict consumed by the /summary endpoint."""
        scores = self.calculate_behavioral_score()
        risk   = self.calculate_risk_score()

        risk_level = "low" if risk < 30 else "medium" if risk < 60 else "high"

        # pick top insight
        domain_scores = {
            "Study": scores["study_score"],
            "Habits": scores["habits_score"],
            "Fitness": scores["fitness_score"],
            "Finance": scores["finance_score"],
            "Goals": scores["goals_score"],
        }
        weakest  = min(domain_scores, key=domain_scores.get)
        strongest = max(domain_scores, key=domain_scores.get)

        top_insight = (
            f"Your {weakest} score ({domain_scores[weakest]:.0f}/100) needs "
            f"attention. Focus here first to improve your overall alignment."
        )

        return {
            "user_id":       self.user_id,
            "overall_score": scores["productivity_score"],
            "financial_score": scores["finance_score"],
            "study_score":   scores["study_score"],
            "habits_score":  scores["habits_score"],
            "fitness_score": scores["fitness_score"],
            "goals_score":   scores["goals_score"],
            "risk_level":    risk_level,
            "top_insight":   top_insight,
            "strongest_domain": strongest,
            "weakest_domain":   weakest,
            "generated_at":  datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # 7. save_snapshot
    # ------------------------------------------------------------------

    def save_snapshot(self, scenario_name: str = "baseline") -> dict[str, Any]:
        """
        Persist current state to simulation_results table and return the
        saved row as a dict.
        """
        from app.core.database import SessionLocal
        from app.models.user import SimulationResult

        state  = self.build_current_state()
        scores = self.calculate_behavioral_score()

        db = SessionLocal()
        try:
            row = SimulationResult(
                user_id=self.user_id,
                scenario_name=scenario_name,
                scenario_type="snapshot",
                input_data=json.dumps({"triggered_by": "user"}),
                result_data=json.dumps(state),
                confidence_score=round(scores["productivity_score"] / 100, 3),
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return {
                "id": row.id,
                "user_id": row.user_id,
                "scenario_name": row.scenario_name,
                "scenario_type": row.scenario_type,
                "confidence_score": row.confidence_score,
                "created_at": row.created_at.isoformat(),
                "result_data": state,
            }
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 8. compare_states
    # ------------------------------------------------------------------

    @staticmethod
    def compare_states(
        state_a: dict[str, Any],
        state_b: dict[str, Any],
        label_a: str = "Current",
        label_b: str = "Projected",
    ) -> dict[str, Any]:
        """
        Produce a delta report between two state dicts.
        Handles nested numeric values recursively.
        """

        def _diff(a: Any, b: Any) -> Any:
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                return round(b - a, 4)
            if isinstance(a, dict) and isinstance(b, dict):
                return {k: _diff(a.get(k, 0), b.get(k, 0)) for k in set(a) | set(b)}
            return b  # non-numeric: just return new value

        return {
            "label_a": label_a,
            "label_b": label_b,
            "state_a": state_a,
            "state_b": state_b,
            "delta":   _diff(state_a, state_b),
            "compared_at": datetime.utcnow().isoformat(),
        }

    # ==================================================================
    # PRIVATE HELPERS
    # ==================================================================

    # ── domain state builders ─────────────────────────────────────────

    def _financial_state(self) -> dict[str, Any]:
        if not self._financial:
            return {
                "total_income": 0, "total_expenses": 0, "net_savings": 0,
                "savings_rate": 0, "top_expense_category": "",
                "monthly_avg_income": 0, "monthly_avg_expenses": 0,
                "record_count": 0,
            }
        income   = sum(r["amount"] for r in self._financial if r["record_type"] == "income")
        expenses = sum(r["amount"] for r in self._financial if r["record_type"] == "expense")

        # monthly average (based on date spread)
        dates = [datetime.fromisoformat(r["date"][:10]) for r in self._financial]
        months = max(1, (max(dates) - min(dates)).days / 30) if dates else 1
        avg_inc  = income   / months
        avg_exp  = expenses / months

        # top expense category
        cat_totals: dict[str, float] = defaultdict(float)
        for r in self._financial:
            if r["record_type"] == "expense":
                cat_totals[r["category"]] += r["amount"]
        top_cat = max(cat_totals, key=cat_totals.get) if cat_totals else ""

        return {
            "total_income":         round(income, 2),
            "total_expenses":       round(expenses, 2),
            "net_savings":          round(income - expenses, 2),
            "savings_rate":         round((income - expenses) / income, 4) if income else 0.0,
            "top_expense_category": top_cat,
            "monthly_avg_income":   round(avg_inc, 2),
            "monthly_avg_expenses": round(avg_exp, 2),
            "record_count":         len(self._financial),
        }

    def _study_state(self) -> dict[str, Any]:
        if not self._study:
            return {
                "avg_study_hours": 0, "avg_focus_score": 0,
                "avg_performance_score": 0, "avg_task_completion": 0,
                "total_sessions": 0, "subjects": [], "study_streak_days": 0,
            }
        n = len(self._study)
        subjects = list({s["subject"] for s in self._study})

        # streak: consecutive days with at least one session (most recent run)
        dates_set = {s["study_date"][:10] for s in self._study}
        today  = datetime.utcnow().date()
        streak = 0
        cur    = today
        while str(cur) in dates_set:
            streak += 1
            cur -= timedelta(days=1)

        return {
            "avg_study_hours":       round(sum(s["study_hours"]       for s in self._study) / n, 2),
            "avg_focus_score":       round(sum(s["focus_score"]       for s in self._study) / n, 1),
            "avg_performance_score": round(sum(s["performance_score"] for s in self._study) / n, 1),
            "avg_task_completion":   round(sum(s["task_completion"]   for s in self._study) / n, 1),
            "total_sessions":        n,
            "subjects":              subjects,
            "study_streak_days":     streak,
        }

    def _habits_state(self) -> dict[str, Any]:
        if not self._habits:
            return {
                "total_habits": 0, "completed_habits": 0,
                "completion_rate": 0, "avg_streak": 0,
                "best_streak": 0, "at_risk_habits": [],
            }
        total     = len(self._habits)
        completed = sum(1 for h in self._habits if h["completed"])
        streaks   = [h["streak"] for h in self._habits]
        at_risk   = [h["name"] for h in self._habits if h["streak"] == 0 and not h["completed"]]

        return {
            "total_habits":    total,
            "completed_habits": completed,
            "completion_rate": round(completed / total, 4),
            "avg_streak":      round(sum(streaks) / total, 1),
            "best_streak":     max(streaks),
            "at_risk_habits":  at_risk,
        }

    def _fitness_state(self) -> dict[str, Any]:
        if not self._fitness:
            return {
                "total_sessions": 0, "avg_duration": 0, "avg_calories": 0,
                "total_calories": 0, "activity_types": [], "sessions_per_week": 0,
            }
        n = len(self._fitness)
        dates = [datetime.fromisoformat(f["activity_date"][:10]) for f in self._fitness]
        weeks = max(1, (max(dates) - min(dates)).days / 7) if dates else 1

        return {
            "total_sessions":   n,
            "avg_duration":     round(sum(f["duration"] for f in self._fitness) / n, 1),
            "avg_calories":     round(sum(f["calories_burned"] for f in self._fitness) / n, 1),
            "total_calories":   round(sum(f["calories_burned"] for f in self._fitness), 1),
            "activity_types":   list({f["activity_type"] for f in self._fitness}),
            "sessions_per_week": round(n / weeks, 2),
        }

    def _goals_state(self) -> list[dict[str, Any]]:
        out = []
        today = datetime.utcnow()
        for g in self._goals:
            target = g["target_value"]
            current = g["current_value"]
            pct = min(100.0, (current / target * 100) if target > 0 else 0)
            try:
                td = datetime.fromisoformat(g["target_date"][:10])
                days_left = (td - today).days
            except Exception:
                days_left = 0

            on_track = pct >= (1 - days_left / max(1, days_left + 1)) * 100 if days_left >= 0 else False
            out.append({
                "id": g["id"], "name": g["name"], "status": g["status"],
                "progress_pct": round(pct, 1),
                "days_remaining": max(0, days_left),
                "on_track": on_track,
            })
        return out

    def _behavioral_patterns(self) -> dict[str, Any]:
        scores = self.calculate_behavioral_score()
        domain_map = {
            "Study":   scores["study_score"],
            "Habits":  scores["habits_score"],
            "Fitness": scores["fitness_score"],
            "Finance": scores["finance_score"],
            "Goals":   scores["goals_score"],
        }
        strongest = max(domain_map, key=domain_map.get)
        weakest   = min(domain_map, key=domain_map.get)
        avg       = sum(domain_map.values()) / len(domain_map)

        if avg >= 70:
            trajectory = "improving"
        elif avg >= 40:
            trajectory = "stable"
        else:
            trajectory = "declining"

        return {
            "consistency_score":  round(scores["habits_score"] * 0.5 + scores["fitness_score"] * 0.5, 1),
            "discipline_score":   round(scores["study_score"] * 0.6 + scores["habits_score"] * 0.4, 1),
            "growth_trajectory":  trajectory,
            "strongest_domain":   strongest,
            "weakest_domain":     weakest,
        }

    # ── domain score calculators (0-100) ─────────────────────────────

    def _study_score(self) -> float:
        if not self._study:
            return 0.0
        n = len(self._study)
        return (
            sum(s["performance_score"] for s in self._study) / n * 0.5
            + sum(s["focus_score"]     for s in self._study) / n * 0.3
            + sum(s["task_completion"] for s in self._study) / n * 0.2
        )

    def _habits_score(self) -> float:
        if not self._habits:
            return 0.0
        total = len(self._habits)
        completed = sum(1 for h in self._habits if h["completed"])
        avg_streak = sum(h["streak"] for h in self._habits) / total
        return min(100.0, (completed / total * 70) + min(30, avg_streak * 2))

    def _fitness_score(self) -> float:
        if not self._fitness:
            return 0.0
        return min(100.0, len(self._fitness) * 10)

    def _finance_score(self) -> float:
        fin = self._financial_state()
        if fin["total_income"] == 0:
            return 0.0
        return min(100.0, max(0.0, fin["savings_rate"] * 400 + 30))

    def _goals_score(self) -> float:
        goals = self._goals_state()
        if not goals:
            return 0.0
        return sum(g["progress_pct"] for g in goals) / len(goals)

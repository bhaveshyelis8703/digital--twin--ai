"""
ml/habit_analysis.py
Habit consistency scorer, productivity index, anomaly detection, 4-week forecast.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression

warnings.filterwarnings("ignore")

_ROOT    = Path(__file__).resolve().parents[1]
_BACKEND = _ROOT / "backend"
_MODELS  = _ROOT / "ml_models" / "trained"
_MODELS.mkdir(parents=True, exist_ok=True)

if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from ml.data_preparation import (
    load_financial_data, load_fitness_data,
    load_habit_data, load_study_data,
)


# ─────────────────────────────────────────────────────────────────────────────
# HABIT CONSISTENCY ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def habit_consistency_score(habits_raw: list[dict]) -> dict:
    """Score 0-100 based on completion rate and streak data."""
    if not habits_raw:
        return {"score": 0, "at_risk": [], "strong": []}

    completed    = sum(1 for h in habits_raw if h.get("completed"))
    total        = len(habits_raw)
    completion_r = completed / total if total else 0
    avg_streak   = np.mean([h.get("streak", 0) for h in habits_raw])
    streak_score = min(avg_streak / 30 * 100, 100)

    score = round(completion_r * 60 + streak_score * 0.4, 1)

    at_risk = [h["name"] for h in habits_raw
               if not h.get("completed") and h.get("streak", 0) < 3]
    strong  = [h["name"] for h in habits_raw
               if h.get("completed") and h.get("streak", 0) >= 7]

    return {
        "score": score,
        "completion_rate": round(completion_r * 100, 1),
        "avg_streak": round(float(avg_streak), 1),
        "at_risk_habits": at_risk,
        "strong_habits":  strong,
        "total_habits":   total,
        "completed_habits": completed,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTIVITY INDEX
# ─────────────────────────────────────────────────────────────────────────────

def compute_productivity_index(
    study_df: pd.DataFrame,
    habits_raw: list[dict],
    fitness_df: pd.DataFrame,
    financial_df: pd.DataFrame,
) -> dict:
    """
    Weighted composite:
      Study task completion  30%
      Habit streak consistency 25%
      Fitness activity freq  20%
      Financial discipline   15%
      Sleep regularity proxy 10%
    """
    # Study component (avg task completion)
    study_score = 0.0
    if not study_df.empty:
        study_score = float(study_df["task_completion"].mean())

    # Habit component
    habit_score = 0.0
    if habits_raw:
        completed = sum(1 for h in habits_raw if h.get("completed"))
        habit_score = completed / len(habits_raw) * 100

    # Fitness component (sessions this month, target 12 = 100%)
    fitness_score = 0.0
    if not fitness_df.empty:
        recent = fitness_df[
            fitness_df["activity_date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)
        ]
        fitness_score = min(len(recent) / 12 * 100, 100)

    # Financial discipline (savings rate)
    finance_score = 0.0
    if not financial_df.empty:
        income  = financial_df[financial_df["record_type"] == "income"]["amount"].sum()
        expense = financial_df[financial_df["record_type"] == "expense"]["amount"].sum()
        if income > 0:
            savings_rate = max((income - expense) / income, 0)
            finance_score = min(savings_rate * 200, 100)  # 50% savings = 100 score

    # Sleep proxy: evening/morning study consistency (heuristic)
    sleep_score = 65.0  # baseline

    index = round(
        study_score   * 0.30 +
        habit_score   * 0.25 +
        fitness_score * 0.20 +
        finance_score * 0.15 +
        sleep_score   * 0.10,
        1,
    )

    return {
        "productivity_index": index,
        "components": {
            "study_task_completion": round(study_score, 1),
            "habit_consistency":     round(habit_score, 1),
            "fitness_frequency":     round(fitness_score, 1),
            "financial_discipline":  round(finance_score, 1),
            "sleep_regularity":      round(sleep_score, 1),
        },
        "interpretation": (
            "Excellent" if index >= 80 else
            "Good"      if index >= 65 else
            "Fair"      if index >= 50 else
            "Needs Improvement"
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# ANOMALY DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_anomalous_weeks(
    study_df: pd.DataFrame,
    fitness_df: pd.DataFrame,
) -> list[dict]:
    """Use Isolation Forest on weekly activity counts to flag unusual weeks."""
    frames = []
    if not study_df.empty:
        study_df = study_df.copy()
        study_df["week"] = study_df["study_date"].dt.to_period("W").apply(lambda x: x.start_time)
        s_weekly = study_df.groupby("week")["study_hours"].sum().rename("study_hours")
        frames.append(s_weekly)

    if not fitness_df.empty:
        fitness_df = fitness_df.copy()
        fitness_df["week"] = fitness_df["activity_date"].dt.to_period("W").apply(lambda x: x.start_time)
        f_weekly = fitness_df.groupby("week")["duration"].sum().rename("fitness_mins")
        frames.append(f_weekly)

    if not frames:
        return []

    combined = pd.concat(frames, axis=1).fillna(0)
    if len(combined) < 8:
        return []

    iso = IsolationForest(contamination=0.1, random_state=42)
    labels = iso.fit_predict(combined.values)

    anomalies = []
    for i, (week, label) in enumerate(zip(combined.index, labels)):
        if label == -1:
            anomalies.append({
                "week": str(week.date()) if hasattr(week, "date") else str(week),
                "study_hours": round(float(combined.iloc[i].get("study_hours", 0)), 1),
                "fitness_mins": round(float(combined.iloc[i].get("fitness_mins", 0)), 1),
                "type": "low_activity" if combined.iloc[i].mean() < combined.mean().mean()
                        else "spike",
            })
    return anomalies


# ─────────────────────────────────────────────────────────────────────────────
# 4-WEEK PRODUCTIVITY FORECAST
# ─────────────────────────────────────────────────────────────────────────────

def forecast_productivity_trend(
    study_df: pd.DataFrame,
    habits_raw: list[dict],
    fitness_df: pd.DataFrame,
    financial_df: pd.DataFrame,
    weeks_ahead: int = 4,
) -> dict:
    """Linear regression on 8-week productivity index → next 4 weeks."""
    weekly_scores = []
    now = pd.Timestamp.now()

    for w in range(8, 0, -1):
        start = now - pd.Timedelta(weeks=w)
        end   = now - pd.Timedelta(weeks=w - 1)

        s_df = study_df[
            (study_df["study_date"] >= start) & (study_df["study_date"] < end)
        ] if not study_df.empty else pd.DataFrame()

        f_df = fitness_df[
            (fitness_df["activity_date"] >= start) & (fitness_df["activity_date"] < end)
        ] if not fitness_df.empty else pd.DataFrame()

        pi = compute_productivity_index(s_df, habits_raw, f_df, financial_df)
        weekly_scores.append(pi["productivity_index"])

    if len(weekly_scores) < 4:
        return {"forecast": [], "trend": "stable"}

    X = np.arange(len(weekly_scores)).reshape(-1, 1)
    lr = LinearRegression().fit(X, weekly_scores)
    slope = float(lr.coef_[0])

    future = []
    for w in range(1, weeks_ahead + 1):
        predicted = float(np.clip(lr.predict([[len(weekly_scores) + w - 1]])[0], 0, 100))
        future.append({
            "week": f"Week +{w}",
            "predicted_index": round(predicted, 1),
        })

    trend = "improving" if slope > 0.5 else "declining" if slope < -0.5 else "stable"
    return {
        "historical": [{"week": f"W-{8-i}", "index": round(s, 1)}
                       for i, s in enumerate(weekly_scores)],
        "forecast": future,
        "trend": trend,
        "slope": round(slope, 3),
    }


# ─────────────────────────────────────────────────────────────────────────────
# FITNESS GOAL PROBABILITY
# ─────────────────────────────────────────────────────────────────────────────

def fitness_goal_probability(fitness_df: pd.DataFrame, days_to_goal: int) -> dict:
    """Estimate probability of hitting a fitness goal based on recent activity."""
    if fitness_df.empty or days_to_goal <= 0:
        return {"probability": 0, "sessions_needed": 0, "on_track": False}

    recent_30 = fitness_df[
        fitness_df["activity_date"] >= pd.Timestamp.now() - pd.Timedelta(days=30)
    ]
    sessions_per_month  = len(recent_30)
    sessions_per_day    = sessions_per_month / 30
    projected_sessions  = sessions_per_day * days_to_goal
    target_sessions     = max(days_to_goal / 3, 1)  # target: every 3 days
    probability         = min(projected_sessions / target_sessions, 1.0)
    on_track            = probability >= 0.7

    return {
        "probability":        round(probability * 100, 1),
        "on_track":           on_track,
        "current_pace":       f"{sessions_per_month:.0f} sessions/month",
        "projected_sessions": round(projected_sessions, 0),
        "target_sessions":    round(target_sessions, 0),
        "interpretation": (
            f"Based on your current pace, you have a {probability*100:.0f}% chance "
            f"of reaching your goal in {days_to_goal} days."
        ),
    }

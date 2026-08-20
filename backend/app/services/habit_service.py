"""
backend/app/services/habit_service.py
Habit analysis service — wraps ml/habit_analysis.py for API use.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_ML   = _ROOT / "ml"
for _p in [str(_ROOT), str(_ML)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


def get_habit_analysis(user_id: int, habits_raw: list[dict]) -> dict:
    """Full habit analysis: consistency score + risk flags."""
    from ml.habit_analysis import habit_consistency_score
    return habit_consistency_score(habits_raw)


def get_productivity_index(user_id: int) -> dict:
    from ml.data_preparation import (
        load_financial_data, load_fitness_data,
        load_habit_data, load_study_data,
    )
    from ml.habit_analysis import compute_productivity_index
    from app.core.database import SessionLocal
    from app.models.user import Habit

    db = SessionLocal()
    try:
        habits_raw = [
            {"name": h.name, "completed": h.completed, "streak": h.streak}
            for h in db.query(Habit).filter(Habit.user_id == user_id).all()
        ]
    finally:
        db.close()

    study_df    = load_study_data(user_id)
    fitness_df  = load_fitness_data(user_id)
    financial_df = load_financial_data(user_id)

    return compute_productivity_index(study_df, habits_raw, fitness_df, financial_df)


def get_productivity_trend(user_id: int) -> dict:
    from ml.data_preparation import (
        load_financial_data, load_fitness_data, load_study_data,
    )
    from ml.habit_analysis import forecast_productivity_trend
    from app.core.database import SessionLocal
    from app.models.user import Habit

    db = SessionLocal()
    try:
        habits_raw = [
            {"name": h.name, "completed": h.completed, "streak": h.streak}
            for h in db.query(Habit).filter(Habit.user_id == user_id).all()
        ]
    finally:
        db.close()

    return forecast_productivity_trend(
        load_study_data(user_id),
        habits_raw,
        load_fitness_data(user_id),
        load_financial_data(user_id),
    )


def get_anomalies(user_id: int) -> list[dict]:
    from ml.data_preparation import load_fitness_data, load_study_data
    from ml.habit_analysis import detect_anomalous_weeks

    return detect_anomalous_weeks(load_study_data(user_id), load_fitness_data(user_id))


def get_fitness_goal_probability(user_id: int, days_to_goal: int) -> dict:
    from ml.data_preparation import load_fitness_data
    from ml.habit_analysis import fitness_goal_probability

    return fitness_goal_probability(load_fitness_data(user_id), days_to_goal)

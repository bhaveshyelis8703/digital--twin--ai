"""
ml/data_preparation.py
Data loading + feature engineering for all 4 domains.
Returns ML-ready pandas DataFrames from SQLite via SQLAlchemy.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.database import SessionLocal
from app.models.user import FinancialRecord, FitnessActivity, Goal, Habit, StudyActivity


# ─────────────────────────────────────────────────────────────────────────────
# RAW LOADERS
# ─────────────────────────────────────────────────────────────────────────────

def load_financial_data(user_id: int) -> pd.DataFrame:
    db = SessionLocal()
    try:
        rows = db.query(FinancialRecord).filter(FinancialRecord.user_id == user_id).all()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "id": r.id, "date": pd.to_datetime(r.date),
            "record_type": r.record_type, "amount": r.amount,
            "description": r.description, "category": r.category,
            "recurring_frequency": r.recurring_frequency,
        } for r in rows])
    finally:
        db.close()


def load_study_data(user_id: int) -> pd.DataFrame:
    db = SessionLocal()
    try:
        rows = db.query(StudyActivity).filter(StudyActivity.user_id == user_id).all()
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame([{
            "id": r.id, "study_date": pd.to_datetime(r.study_date),
            "subject": r.subject, "study_hours": r.study_hours,
            "focus_score": r.focus_score, "task_completion": r.task_completion,
            "performance_score": r.performance_score,
        } for r in rows])
    finally:
        db.close()


def load_habit_data(user_id: int) -> pd.DataFrame:
    """Return habits aggregated by week."""
    db = SessionLocal()
    try:
        rows = db.query(Habit).filter(Habit.user_id == user_id).all()
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame([{
            "id": r.id, "name": r.name,
            "target_frequency": r.target_frequency,
            "completed": int(r.completed), "streak": r.streak,
            "created_at": pd.to_datetime(r.created_at),
        } for r in rows])
        # week-level aggregation
        df["week"] = df["created_at"].dt.to_period("W").apply(lambda x: x.start_time)
        weekly = df.groupby("week").agg(
            total_habits=("id", "count"),
            completed_habits=("completed", "sum"),
            avg_streak=("streak", "mean"),
        ).reset_index()
        weekly["completion_rate"] = weekly["completed_habits"] / weekly["total_habits"]
        return weekly
    finally:
        db.close()


def load_fitness_data(user_id: int) -> pd.DataFrame:
    """Return fitness activities with rolling 7-day averages."""
    db = SessionLocal()
    try:
        rows = db.query(FitnessActivity).filter(FitnessActivity.user_id == user_id).all()
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame([{
            "id": r.id, "activity_date": pd.to_datetime(r.activity_date),
            "activity_type": r.activity_type, "duration": r.duration,
            "calories_burned": r.calories_burned,
        } for r in rows]).sort_values("activity_date")
        df["rolling_avg_calories"] = df["calories_burned"].rolling(7, min_periods=1).mean()
        df["rolling_avg_duration"] = df["duration"].rolling(7, min_periods=1).mean()
        return df
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def engineer_financial_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add ML features to financial DataFrame."""
    if df.empty:
        return df
    df = df.sort_values("date").copy()
    df["month"] = df["date"].dt.month
    df["year"]  = df["date"].dt.year
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_income"] = (df["record_type"] == "income").astype(int)

    # monthly income and expenses
    inc_m = (
        df[df["record_type"] == "income"]
        .groupby(["year", "month"])["amount"].sum()
        .rename("income")
    )
    exp_m = (
        df[df["record_type"] == "expense"]
        .groupby(["year", "month"])["amount"].sum()
        .rename("expenses")
    )
    monthly = pd.concat([inc_m, exp_m], axis=1).fillna(0).reset_index()
    monthly["net_savings"]        = monthly["income"] - monthly["expenses"]
    monthly["expense_to_income"]  = np.where(
        monthly["income"] > 0, monthly["expenses"] / monthly["income"], 1.0
    )
    monthly["date"] = pd.to_datetime(
        monthly["year"].astype(str) + "-" + monthly["month"].astype(str).str.zfill(2) + "-01"
    )
    monthly = monthly.sort_values("date").reset_index(drop=True)
    monthly["rolling_3mo_avg"] = monthly["net_savings"].rolling(3, min_periods=1).mean()
    monthly["mom_growth"]      = monthly["net_savings"].pct_change().fillna(0).clip(-5, 5)
    monthly["savings_rate"]    = monthly["net_savings"] / (monthly["net_savings"].abs() + 1)
    return monthly


def engineer_study_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.sort_values("study_date").copy()
    df["month"] = df["study_date"].dt.month
    df["day_of_week"] = df["study_date"].dt.dayofweek
    df["week_num"] = df["study_date"].dt.isocalendar().week.astype(int)

    # weekly aggregates
    df["week"] = df["study_date"].dt.to_period("W").apply(lambda x: x.start_time)
    weekly = df.groupby("week").agg(
        weekly_hours=("study_hours", "sum"),
        avg_focus=("focus_score", "mean"),
        avg_task_completion=("task_completion", "mean"),
        avg_performance=("performance_score", "mean"),
        sessions=("id", "count"),
    ).reset_index()
    weekly["hours_trend"] = weekly["weekly_hours"].diff().fillna(0)
    weekly["study_streak"] = (weekly["sessions"] > 0).astype(int).cumsum()
    weekly["subject_encoded"] = 0  # placeholder — encoded per training set
    return weekly


def engineer_habit_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["streak_squared"] = df["avg_streak"] ** 2
    df["week_num"] = pd.to_datetime(df["week"]).dt.isocalendar().week.astype(int)
    df["lag1_completion"] = df["completion_rate"].shift(1).fillna(df["completion_rate"].mean())
    return df

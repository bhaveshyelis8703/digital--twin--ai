"""
ml/study_prediction.py
Random Forest performance predictor, exam readiness, optimal study plan.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

_ROOT    = Path(__file__).resolve().parents[1]
_BACKEND = _ROOT / "backend"
_MODELS  = _ROOT / "ml_models" / "trained"
_MODELS.mkdir(parents=True, exist_ok=True)

if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from ml.data_preparation import load_study_data


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_study_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    if df.empty or len(df) < 5:
        return pd.DataFrame(), pd.Series(dtype=float)

    df = df.sort_values("study_date").copy()
    le = LabelEncoder()
    df["subject_encoded"] = le.fit_transform(df["subject"].astype(str))
    df["month"]           = df["study_date"].dt.month
    df["day_of_week"]     = df["study_date"].dt.dayofweek
    df["week_num"]        = df["study_date"].dt.isocalendar().week.astype(int)

    # rolling study streak (days with a session in last 7 calendar days)
    df = df.reset_index(drop=True)
    df["study_streak_days"] = df["study_date"].apply(
        lambda d: df[
            (df["study_date"] <= d) &
            (df["study_date"] >= d - pd.Timedelta(days=7))
        ].shape[0]
    )
    df["peak_study_hour"] = df["study_date"].dt.hour

    feature_cols = [
        "study_hours", "focus_score", "task_completion",
        "subject_encoded", "month", "day_of_week",
        "study_streak_days", "peak_study_hour",
    ]
    X = df[feature_cols]
    y = df["performance_score"]
    return X, y


# ─────────────────────────────────────────────────────────────────────────────
# TRAIN
# ─────────────────────────────────────────────────────────────────────────────

def train_study_model(user_id: int | None = None,
                      training_df: pd.DataFrame | None = None) -> dict:
    if training_df is None and user_id is not None:
        training_df = load_study_data(user_id)

    if training_df is None or training_df.empty:
        return {"status": "no_data"}

    X, y = build_study_features(training_df)
    if X.empty or len(X) < 8:
        return {"status": "insufficient_data", "n": len(X)}

    rf = RandomForestRegressor(
        n_estimators=200, max_depth=10,
        min_samples_leaf=1, min_samples_split=2,
        random_state=42, n_jobs=-1,
    )

    # Cross-validation
    cv = KFold(n_splits=min(5, len(X) // 2), shuffle=True, random_state=42)
    cv_r2 = cross_val_score(rf, X, y, cv=cv, scoring="r2")

    # final fit
    rf.fit(X, y)
    pred  = rf.predict(X)
    r2    = r2_score(y, pred)
    rmse  = float(np.sqrt(mean_squared_error(y, pred)))

    suffix = f"user_{user_id}" if user_id else "global"
    path   = _MODELS / f"study_rf_model_{suffix}.pkl"
    meta   = {
        "feature_cols": list(X.columns),
        "label_encoder_classes": list(pd.get_dummies(
            training_df["subject"].astype(str)).columns),
    }
    joblib.dump({"model": rf, "meta": meta}, path)
    return {
        "status": "ok", "model_path": str(path),
        "metrics": {
            "R2": round(r2, 4),
            "RMSE": round(rmse, 2),
            "CV_R2_mean": round(float(cv_r2.mean()), 4),
            "CV_R2_std":  round(float(cv_r2.std()), 4),
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# PREDICTION FUNCTIONS  (used by study_service.py)
# ─────────────────────────────────────────────────────────────────────────────

def predict_performance(model_bundle: dict, input_features: dict) -> float:
    model = model_bundle["model"]
    meta  = model_bundle["meta"]
    row   = pd.DataFrame([{c: input_features.get(c, 0) for c in meta["feature_cols"]}])
    pred  = float(np.clip(model.predict(row)[0], 0, 100))
    return round(pred, 1)


def exam_readiness_score(df: pd.DataFrame) -> dict:
    """Composite score: focus (40%) + task_completion (35%) + hours_rate (25%)."""
    if df.empty:
        return {"score": 0, "breakdown": {}, "interpretation": "No data"}

    recent = df.sort_values("study_date").tail(14)  # last 2 weeks
    avg_focus   = float(recent["focus_score"].mean())
    avg_task    = float(recent["task_completion"].mean())
    avg_hours   = float(recent["study_hours"].mean())
    hours_score = min(avg_hours / 4.0 * 100, 100)  # 4h/session = 100%

    score = round(avg_focus * 0.40 + avg_task * 0.35 + hours_score * 0.25, 1)
    interpretation = (
        "Excellent" if score >= 85 else
        "Good" if score >= 70 else
        "Fair" if score >= 55 else
        "Needs Improvement"
    )
    return {
        "score": score,
        "interpretation": interpretation,
        "breakdown": {
            "focus_contribution":      round(avg_focus * 0.40, 1),
            "task_completion_contribution": round(avg_task * 0.35, 1),
            "hours_contribution":      round(hours_score * 0.25, 1),
        },
        "avg_focus":   round(avg_focus, 1),
        "avg_task":    round(avg_task, 1),
        "avg_hours":   round(avg_hours, 2),
    }


def optimal_study_plan(target_score: float, days_until_exam: int,
                       current_score: float = 60.0) -> dict:
    """Calculate recommended daily study hours to reach target_score."""
    if days_until_exam <= 0:
        return {"error": "Exam date must be in the future"}

    gap            = max(target_score - current_score, 0)
    base_hours     = 1.5
    extra_per_point = 0.05
    daily_hours    = min(base_hours + gap * extra_per_point, 8.0)
    total_hours    = daily_hours * days_until_exam

    sessions_per_day = max(1, round(daily_hours / 2))
    session_length   = round(daily_hours / sessions_per_day, 1)

    return {
        "recommended_daily_hours": round(daily_hours, 1),
        "sessions_per_day":        sessions_per_day,
        "session_length_hours":    session_length,
        "total_study_hours":       round(total_hours, 1),
        "current_score":           current_score,
        "target_score":            target_score,
        "days_until_exam":         days_until_exam,
        "feasibility":             "Achievable" if daily_hours <= 6 else "Challenging",
    }


def study_trend(df: pd.DataFrame) -> dict:
    """Linear regression on weekly study hours — returning trend direction."""
    if df.empty or len(df) < 4:
        return {"trend": "stable", "slope": 0, "description": "Insufficient data"}

    df = df.sort_values("study_date").copy()
    df["week"] = df["study_date"].dt.to_period("W").apply(lambda x: x.start_time)
    weekly = df.groupby("week")["study_hours"].sum().reset_index()
    weekly["week_num"] = range(len(weekly))

    lr = LinearRegression()
    lr.fit(weekly[["week_num"]], weekly["study_hours"])
    slope = float(lr.coef_[0])

    trend = "improving" if slope > 0.1 else "declining" if slope < -0.1 else "stable"
    return {
        "trend": trend,
        "slope": round(slope, 3),
        "description": (
            f"Study hours are {trend} by {abs(slope):.2f}h/week on average."
        ),
        "weekly_data": weekly.rename(columns={"week": "date", "study_hours": "hours"})
                             .assign(date=lambda d: d["date"].astype(str))[["date","hours"]]
                             .to_dict(orient="records"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL TRAINER (called by train_all.py)
# ─────────────────────────────────────────────────────────────────────────────

def train_global_study_model(sample_user_ids: list[int]) -> dict:
    frames = []
    for uid in sample_user_ids:
        df = load_study_data(uid)
        if not df.empty:
            frames.append(df)
    if not frames:
        return {"status": "no_data"}
    combined = pd.concat(frames, ignore_index=True)
    return train_study_model(training_df=combined)

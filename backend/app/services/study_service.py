"""
backend/app/services/study_service.py
Study prediction service — wraps ml/study_prediction.py for API use.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_ROOT    = Path(__file__).resolve().parents[3]
_ML      = _ROOT / "ml"
_MODELS  = _ROOT / "ml_models" / "trained"

for _p in [str(_ROOT), str(_ML)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

_MODEL_CACHE: dict[str, Any] = {}


def _load_study_model(user_id: int | None = None) -> dict | None:
    key = f"study_rf_user_{user_id}" if user_id else "study_rf_global"
    if key in _MODEL_CACHE:
        return _MODEL_CACHE[key]

    # try user-specific, then global
    candidates = []
    if user_id:
        candidates.append(_MODELS / f"study_rf_model_user_{user_id}.pkl")
    candidates.append(_MODELS / "study_rf_model_global.pkl")

    for path in candidates:
        if path.exists():
            try:
                import joblib
                bundle = joblib.load(path)
                _MODEL_CACHE[key] = bundle
                return bundle
            except Exception:
                continue
    return None


def get_performance_prediction(user_id: int, input_features: dict) -> dict:
    """Predict performance score for given study input."""
    from ml.study_prediction import predict_performance

    bundle = _load_study_model(user_id)
    if bundle is None:
        # fallback: heuristic from inputs
        hours  = float(input_features.get("study_hours", 2))
        focus  = float(input_features.get("focus_score", 70))
        task   = float(input_features.get("task_completion", 70))
        score  = min(focus * 0.4 + task * 0.35 + hours * 3, 100)
        return {"predicted_score": round(score, 1), "source": "heuristic"}

    score = predict_performance(bundle, input_features)
    return {"predicted_score": score, "source": "ml_model"}


def get_exam_readiness(user_id: int) -> dict:
    from ml.data_preparation import load_study_data
    from ml.study_prediction import exam_readiness_score

    df = load_study_data(user_id)
    return exam_readiness_score(df)


def get_optimal_plan(target_score: float, exam_date_str: str,
                     subject: str, user_id: int) -> dict:
    from datetime import datetime
    from ml.data_preparation import load_study_data
    from ml.study_prediction import exam_readiness_score, optimal_study_plan

    df = load_study_data(user_id)
    readiness    = exam_readiness_score(df)
    current_score = readiness.get("score", 60.0)

    try:
        exam_dt   = datetime.fromisoformat(exam_date_str)
        days_left = max((exam_dt - datetime.now()).days, 1)
    except Exception:
        days_left = 30

    plan = optimal_study_plan(target_score, days_left, current_score)
    plan["subject"] = subject
    plan["current_readiness"] = readiness
    return plan


def get_study_trend(user_id: int) -> dict:
    from ml.data_preparation import load_study_data
    from ml.study_prediction import study_trend

    df = load_study_data(user_id)
    return study_trend(df)

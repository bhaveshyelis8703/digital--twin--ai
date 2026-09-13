"""
ml/financial_forecasting.py
Three financial forecasting models:
  1. Prophet  — savings projection (6/12/36 months)
  2. XGBoost  — per-category expense forecasting
  3. ARIMA    — monthly cash flow
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import Ridge
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

_ROOT    = Path(__file__).resolve().parents[1]
_BACKEND = _ROOT / "backend"
_MODELS  = _ROOT / "ml_models" / "trained"
_MODELS.mkdir(parents=True, exist_ok=True)

if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from ml.data_preparation import engineer_financial_features, load_financial_data

EXPENSE_CATEGORIES = [
    "Education", "Entertainment", "Fitness", "Food", "Healthcare",
    "Housing", "Shopping", "Transport", "Utilities",
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def safe_mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1.0) -> float:
    """Robust MAPE that avoids divide-by-zero and extreme inflation near zero.

    We use a floor on the absolute actual value, so near-zero savings periods do not
    create meaningless percentage errors. This is a standard, defensible treatment for
    financial series where actuals can legitimately be zero or close to zero.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    denom = np.maximum(np.abs(y_true), eps)
    valid = np.isfinite(y_true) & np.isfinite(y_pred)
    if not np.any(valid):
        return 0.0
    pct = np.abs((y_true[valid] - y_pred[valid]) / denom[valid]) * 100.0
    return float(np.mean(pct)) if len(pct) else 0.0


def summarize_savings_metrics(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1.0) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    valid = np.isfinite(y_true) & np.isfinite(y_pred)
    y_true = y_true[valid]
    y_pred = y_pred[valid]
    if len(y_true) == 0:
        return {"MAE": 0.0, "RMSE": 0.0, "MAPE": 0.0, "R2": 0.0, "valid_samples": 0}
    if len(y_true) < 2:
        r2 = 0.0
    else:
        try:
            r2 = float(r2_score(y_true, y_pred))
        except Exception:
            r2 = 0.0
    return {
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAPE": float(safe_mape(y_true, y_pred, eps=eps)),
        "R2": r2,
        "valid_samples": int(len(y_true)),
    }


def _mape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1.0) -> float:
    return safe_mape(y_true, y_pred, eps=eps)


def _build_monthly_series(user_id: int) -> pd.DataFrame:
    """Return monthly net-savings series ready for Prophet (ds, y)."""
    df = load_financial_data(user_id)
    if df.empty:
        return pd.DataFrame(columns=["ds", "y"])
    feat = engineer_financial_features(df)
    if feat.empty:
        return pd.DataFrame(columns=["ds", "y"])
    result = feat[["date", "net_savings"]].rename(columns={"date": "ds", "net_savings": "y"})
    return result.sort_values("ds").reset_index(drop=True)


def _build_savings_rate_frame(df: pd.DataFrame) -> pd.DataFrame:
    monthly = engineer_financial_features(df)
    if monthly.empty or (monthly["income"] <= 0).all():
        return pd.DataFrame()
    monthly = monthly.copy()
    monthly["savings_rate_target"] = monthly["net_savings"] / monthly["income"].clip(lower=1)
    monthly["savings_rate"] = monthly["savings_rate_target"]
    monthly["month_sin"] = np.sin(2 * np.pi * monthly["date"].dt.month / 12)
    monthly["month_cos"] = np.cos(2 * np.pi * monthly["date"].dt.month / 12)
    monthly["trend"] = np.arange(len(monthly), dtype=float)
    return monthly


def train_global_savings_regression(sample_user_ids: list[int]) -> dict:
    """Train a pooled savings-rate model that is invariant to user income scale."""
    frames = []
    for uid in sample_user_ids:
        df = load_financial_data(uid)
        if not df.empty:
            frame = _build_savings_rate_frame(df)
            if len(frame) >= 4:
                frames.append(frame)
    if not frames:
        return {"status": "no_data"}

    for stale in list(_MODELS.glob("savings_prophet*.pkl")):
        stale.unlink(missing_ok=True)

    combined = pd.concat(frames, ignore_index=True)
    feature_cols = ["month_sin", "month_cos", "trend"]
    model = Ridge(alpha=1.0)
    model.fit(combined[feature_cols], combined["savings_rate_target"])
    residuals = combined["savings_rate_target"] - model.predict(combined[feature_cols])
    bundle = {
        "model": model,
        "feature_cols": feature_cols,
        "residual_std": float(residuals.std()),
    }
    path = _MODELS / "savings_regression.pkl"
    # Remove stale Prophet artifacts so the benchmark cannot silently fall back to them.
    for stale in list(_MODELS.glob("savings_prophet*.pkl")):
        stale.unlink(missing_ok=True)
    joblib.dump(bundle, path)
    return {"status": "ok", "model_path": str(path), "samples": len(combined)}


# ─────────────────────────────────────────────────────────────────────────────
# 1. PROPHET — SAVINGS PROJECTION
# ─────────────────────────────────────────────────────────────────────────────

def train_savings_prophet(training_df: pd.DataFrame) -> Any:
    """Train a Prophet model on monthly savings. Returns fitted model."""
    from prophet import Prophet  # lazy import — heavy

    if len(training_df) < 3:
        return None

    m = Prophet(
        yearly_seasonality=len(training_df) >= 24,
        weekly_seasonality=False,
        daily_seasonality=False,
        seasonality_mode="multiplicative",
        changepoint_prior_scale=0.05,
        interval_width=0.80,
    )
    m.fit(training_df)
    return m


def forecast_savings(model: Any, months: int) -> pd.DataFrame:
    """Return forecast DataFrame: date, predicted_savings, lower_bound, upper_bound."""
    future = model.make_future_dataframe(periods=months, freq="MS")
    forecast = model.predict(future)
    out = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(months).copy()
    out.columns = ["date", "predicted_savings", "lower_bound", "upper_bound"]
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out


def train_and_save_prophet_for_user(user_id: int) -> dict:
    """Train Prophet on a specific user's data and persist."""
    series = _build_monthly_series(user_id)
    if len(series) < 3:
        return {"status": "insufficient_data", "n_months": len(series)}

    split = max(2, len(series) - 2)
    train, test = series.iloc[:split], series.iloc[split:]
    model = train_savings_prophet(train)
    if model is None:
        return {"status": "training_failed"}

    # evaluate on held-out months
    metrics = {}
    if not test.empty:
        fc = forecast_savings(model, len(test))
        mae  = mean_absolute_error(test["y"].values, fc["predicted_savings"].values)
        rmse = np.sqrt(mean_squared_error(test["y"].values, fc["predicted_savings"].values))
        mape = _mape(test["y"].values, fc["predicted_savings"].values)
        metrics = {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE": round(mape, 2)}

    # retrain on full data
    full_model = train_savings_prophet(series)
    path = _MODELS / f"savings_prophet_user_{user_id}.pkl"
    joblib.dump(full_model, path)
    return {"status": "ok", "model_path": str(path), "metrics": metrics}


# ─────────────────────────────────────────────────────────────────────────────
# 2. XGBOOST — EXPENSE CATEGORY FORECASTING
# ─────────────────────────────────────────────────────────────────────────────

def build_expense_features(
    df: pd.DataFrame, category_classes: list[str] | None = None
) -> tuple[pd.DataFrame, pd.Series]:
    """Build feature matrix for XGBoost expense forecasting."""
    exp = df[df["record_type"] == "expense"].copy()
    if exp.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    exp = exp.sort_values("date")
    exp["month"]       = exp["date"].dt.month
    exp["year"]        = exp["date"].dt.year
    exp["day_of_week"] = exp["date"].dt.dayofweek

    classes = category_classes or EXPENSE_CATEGORIES
    category_map = {category: index for index, category in enumerate(classes)}
    exp["category_enc"] = (
        exp["category"].astype(str).map(category_map).fillna(-1).astype(int)
    )

    # monthly rolling avg per category
    monthly_cat = (
        exp.groupby(["year", "month", "category"])["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "cat_monthly_total"})
    )
    monthly_cat["rolling_3mo"] = monthly_cat.groupby("category")["cat_monthly_total"].transform(
        lambda x: x.shift(1).rolling(3, min_periods=1).mean()
    )
    exp = exp.merge(
        monthly_cat[["year", "month", "category", "rolling_3mo"]],
        on=["year", "month", "category"], how="left",
    )

    # monthly income — group on integer columns, not Series
    inc_df = df[df["record_type"] == "income"].copy()
    inc_df["year"]  = inc_df["date"].dt.year
    inc_df["month"] = inc_df["date"].dt.month
    inc = (
        inc_df.groupby(["year", "month"])["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "income_this_month"})
    )
    inc["income_this_month"] = inc["income_this_month"].shift(1)
    exp = exp.merge(inc, on=["year", "month"], how="left").fillna(0)

    feature_cols = ["month", "day_of_week", "rolling_3mo", "category_enc", "income_this_month"]
    X = exp[feature_cols]
    y = exp["amount"]
    return X, y


def train_expense_xgb(user_id: int) -> dict:
    from xgboost import XGBRegressor
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    df = load_financial_data(user_id)
    if df.empty:
        return {"status": "no_data"}

    X, y = build_expense_features(df)
    if X.empty or len(X) < 10:
        return {"status": "insufficient_data"}

    split = int(len(X) * 0.8)
    X_tr, X_te = X.iloc[:split], X.iloc[split:]
    y_tr, y_te = y.iloc[:split], y.iloc[split:]

    def objective(trial: optuna.Trial) -> float:
        params = {
            "n_estimators":    trial.suggest_int("n_estimators", 50, 200),
            "max_depth":       trial.suggest_int("max_depth", 2, 6),
            "learning_rate":   trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "subsample":       trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree":trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "random_state": 42,
        }
        model = XGBRegressor(**params)
        tss = TimeSeriesSplit(n_splits=3)
        scores = []
        for tr_i, val_i in tss.split(X_tr):
            model.fit(X_tr.iloc[tr_i], y_tr.iloc[tr_i])
            pred = model.predict(X_tr.iloc[val_i])
            scores.append(mean_squared_error(y_tr.iloc[val_i], pred))
        return float(np.mean(scores))

    study = optuna.create_study(direction="minimize")
    n_trials = min(30, max(5, len(X) // 5))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best = XGBRegressor(**study.best_params, random_state=42)
    best.fit(X_tr, y_tr)
    pred = best.predict(X_te)
    mape = _mape(y_te.values, pred)
    rmse = np.sqrt(mean_squared_error(y_te, pred))

    path = _MODELS / f"expense_xgb_user_{user_id}.pkl"
    joblib.dump(best, path)
    return {
        "status": "ok", "model_path": str(path),
        "metrics": {"MAPE": round(mape, 2), "RMSE": round(rmse, 2)},
        "best_params": study.best_params,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. ARIMA — CASH FLOW
# ─────────────────────────────────────────────────────────────────────────────

def train_cashflow_arima(user_id: int) -> dict:
    from statsmodels.tsa.arima.model import ARIMA
    import itertools

    series = _build_monthly_series(user_id)
    if len(series) < 6:
        return {"status": "insufficient_data"}

    y = series["y"].values
    split = len(y) - 2
    train, test = y[:split], y[split:]

    # grid search for best AIC
    best_aic, best_order, best_model = np.inf, (1, 1, 1), None
    for p, d, q in itertools.product(range(3), range(2), range(3)):
        try:
            m = ARIMA(train, order=(p, d, q)).fit()
            if m.aic < best_aic:
                best_aic, best_order, best_model = m.aic, (p, d, q), m
        except Exception:
            continue

    if best_model is None:
        return {"status": "arima_failed"}

    # evaluate
    forecast = best_model.forecast(steps=len(test))
    mape = _mape(test, forecast)
    rmse = np.sqrt(mean_squared_error(test, forecast))

    # retrain on full
    final = ARIMA(y, order=best_order).fit()
    path = _MODELS / f"cashflow_arima_user_{user_id}.pkl"
    joblib.dump({"model": final, "order": best_order}, path)
    return {
        "status": "ok", "model_path": str(path), "order": best_order,
        "metrics": {"MAPE": round(mape, 2), "RMSE": round(rmse, 2), "AIC": round(best_aic, 2)},
    }


# ─────────────────────────────────────────────────────────────────────────────
# SHARED GENERIC TRAINER  (used by train_all.py for global model on synth data)
# ─────────────────────────────────────────────────────────────────────────────

def train_global_models(sample_user_ids: list[int]) -> dict:
    """Train one Prophet + XGBoost on pooled data from sample users."""
    from prophet import Prophet
    from xgboost import XGBRegressor

    all_series, all_X, all_y = [], [], []
    for uid in sample_user_ids:
        s = _build_monthly_series(uid)
        if len(s) >= 3:
            all_series.append(s)
        df = load_financial_data(uid)
        if not df.empty:
            X, y = build_expense_features(df, category_classes=EXPENSE_CATEGORIES)
            if not X.empty:
                all_X.append(X)
                all_y.append(y)

    results = {}

    # Global Prophet is disabled when the normalized savings-rate regression is active.
    if (_MODELS / "savings_regression.pkl").exists():
        results["prophet"] = "disabled: savings_regression active"
    elif all_series:
        combined = pd.concat(all_series, ignore_index=True).sort_values("ds")
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False,
                    daily_seasonality=False, interval_width=0.80)
        m.fit(combined)
        path = _MODELS / "savings_prophet.pkl"
        joblib.dump(m, path)
        results["prophet"] = str(path)

    # Global XGBoost
    if all_X:
        X_all = pd.concat(all_X, ignore_index=True)
        y_all = pd.concat(all_y, ignore_index=True)
        split = int(len(X_all) * 0.8)
        xgb = XGBRegressor(
            n_estimators=250, max_depth=3, learning_rate=0.04,
            min_child_weight=3, subsample=0.85, colsample_bytree=0.9,
            reg_alpha=0.05, reg_lambda=2.0, random_state=42,
        )
        xgb.fit(X_all.iloc[:split], y_all.iloc[:split])
        pred = xgb.predict(X_all.iloc[split:])
        mape = _mape(y_all.iloc[split:].values, pred)
        path = _MODELS / "expense_xgb.pkl"
        joblib.dump(xgb, path)
        results["xgb"] = {"path": str(path), "MAPE": round(mape, 2)}

    return results

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
from sklearn.metrics import mean_absolute_error, mean_squared_error
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


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


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


# ─────────────────────────────────────────────────────────────────────────────
# 1. PROPHET — SAVINGS PROJECTION
# ─────────────────────────────────────────────────────────────────────────────

def train_savings_prophet(training_df: pd.DataFrame) -> Any:
    """Train a Prophet model on monthly savings. Returns fitted model."""
    from prophet import Prophet  # lazy import — heavy

    if len(training_df) < 3:
        return None

    m = Prophet(
        yearly_seasonality=True,
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

def build_expense_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Build feature matrix for XGBoost expense forecasting."""
    exp = df[df["record_type"] == "expense"].copy()
    if exp.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    exp = exp.sort_values("date")
    exp["month"]       = exp["date"].dt.month
    exp["year"]        = exp["date"].dt.year
    exp["day_of_week"] = exp["date"].dt.dayofweek

    le = LabelEncoder()
    exp["category_enc"] = le.fit_transform(exp["category"].astype(str))

    # monthly rolling avg per category
    monthly_cat = (
        exp.groupby(["year", "month", "category"])["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "cat_monthly_total"})
    )
    monthly_cat["rolling_3mo"] = monthly_cat.groupby("category")["cat_monthly_total"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
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
            X, y = build_expense_features(df)
            if not X.empty:
                all_X.append(X)
                all_y.append(y)

    results = {}

    # Global Prophet
    if all_series:
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
        xgb = XGBRegressor(n_estimators=100, max_depth=4,
                           learning_rate=0.1, random_state=42)
        xgb.fit(X_all.iloc[:split], y_all.iloc[:split])
        pred = xgb.predict(X_all.iloc[split:])
        mape = _mape(y_all.iloc[split:].values, pred)
        path = _MODELS / "expense_xgb.pkl"
        joblib.dump(xgb, path)
        results["xgb"] = {"path": str(path), "MAPE": round(mape, 2)}

    return results

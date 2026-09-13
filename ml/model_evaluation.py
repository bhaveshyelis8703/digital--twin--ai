"""
ml/model_evaluation.py  Milestone 2
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import ExtraTreesRegressor

_ROOT    = Path(__file__).resolve().parents[1]
_BACKEND = _ROOT / "backend"
_MODELS  = _ROOT / "ml_models" / "trained"
_DOCS    = _ROOT / "docs"
_DOCS.mkdir(exist_ok=True)
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ml.data_preparation import load_financial_data, load_study_data
from ml.financial_forecasting import (
    EXPENSE_CATEGORIES, _build_monthly_series, _mape, build_expense_features,
    _build_savings_rate_frame, summarize_savings_metrics, train_savings_prophet,
)
from ml.study_prediction import build_study_features


def evaluate_all(test_user_ids):
    results = {}
    regression_path = _MODELS / "savings_regression.pkl"
    if regression_path.exists():
        bundle = joblib.load(regression_path)
        model = bundle["model"]
        all_maes, all_rmses, all_mapes, all_r2s, valid = [], [], [], [], 0
        for uid in test_user_ids:
            df = load_financial_data(uid)
            frame = _build_savings_rate_frame(df) if not df.empty else pd.DataFrame()
            if len(frame) < 6:
                continue
            split = len(frame) - 2
            train, test = frame.iloc[:split], frame.iloc[split:]
            if len(test) == 0:
                continue
            features = test[["month_sin", "month_cos", "trend"]]
            rates = np.clip(model.predict(features), -2, 1)
            income = float(train["income"].median())
            y_true = test["net_savings"].to_numpy()
            y_pred = rates * income
            metrics = summarize_savings_metrics(y_true, y_pred, eps=1.0)
            valid += 1
            all_maes.append(metrics["MAE"])
            all_rmses.append(metrics["RMSE"])
            all_mapes.append(metrics["MAPE"])
            all_r2s.append(metrics["R2"])
        if all_maes:
            avg_mape = float(np.median(all_mapes))
            avg_r2 = float(np.median(all_r2s)) if all_r2s else 0.0
            results["savings_regression"] = {
                "MAE": round(float(np.mean(all_maes)), 2),
                "RMSE": round(float(np.mean(all_rmses)), 2),
                "MAPE": round(avg_mape, 2),
                "R2": round(avg_r2, 4),
                "accuracy_pct": round(max(100 - avg_mape, 0), 1),
                "users_evaluated": valid,
                "meets_target": avg_mape <= 15,
            }

    prophet_path = _MODELS / "savings_prophet.pkl"
    if prophet_path.exists():
        maes, mapes, rmses, valid = [], [], [], 0
        for uid in test_user_ids:
            s = _build_monthly_series(uid)
            if len(s) < 6:
                continue
            split = len(s) - 2
            train, test = s.iloc[:split], s.iloc[split:]
            model = train_savings_prophet(train)
            if model is None:
                continue
            fc = model.predict(test[["ds"]])
            y_true = test["y"].values
            y_pred = fc["yhat"].values
            if np.all(np.abs(y_true) < 1):
                continue
            valid += 1
            maes.append(mean_absolute_error(y_true, y_pred))
            rmses.append(np.sqrt(mean_squared_error(y_true, y_pred)))
            mapes.append(_mape(y_true, y_pred, eps=1.0))
        if maes:
            avg_mape = float(np.median(mapes))
            results["savings_personalized"] = {"MAE": round(float(np.mean(maes)),2),
                "RMSE": round(float(np.mean(rmses)),2), "MAPE": round(avg_mape,2),
                "accuracy_pct": round(max(100-avg_mape,0),1), "users_evaluated": valid,
                "meets_target": avg_mape <= 15}
    xgb_path = _MODELS / "expense_xgb.pkl"
    if xgb_path.exists():
        model = joblib.load(xgb_path)
        maes, mapes, rmses = [], [], []
        for uid in test_user_ids:
            df = load_financial_data(uid)
            if df.empty: continue
            X, y = build_expense_features(df, category_classes=EXPENSE_CATEGORIES)
            if X.empty or len(X) < 10: continue
            split = int(len(X)*0.8)
            if split >= len(X): continue
            pred = model.predict(X.iloc[split:])
            y_t  = y.iloc[split:].values
            maes.append(mean_absolute_error(y_t, pred))
            rmses.append(np.sqrt(mean_squared_error(y_t, pred)))
            mapes.append(_mape(y_t, pred))
        if maes:
            avg_mape = float(np.median(mapes))
            results["expense_xgb"] = {"MAE": round(float(np.mean(maes)),2),
                "RMSE": round(float(np.mean(rmses)),2), "MAPE_median": round(avg_mape,2),
                "accuracy_pct": round(max(100-avg_mape,0),1), "meets_target": avg_mape<=15}
    study_path = _MODELS / "study_rf_model_global.pkl"
    if study_path.exists():
        r2s, rmses, y_true_all, y_pred_all = [], [], [], []
        for uid in test_user_ids:
            df = load_study_data(uid)
            if df.empty: continue
            classes = sorted(df["subject"].astype(str).unique())
            X, y = build_study_features(df, subject_classes=classes)
            if X.empty or len(X) < 10: continue
            split = int(len(X)*0.8)
            if split >= len(X): continue
            model = ExtraTreesRegressor(
                n_estimators=300, max_depth=12, min_samples_leaf=2,
                max_features=0.85, random_state=42, n_jobs=-1,
            )
            model.fit(X.iloc[:split], y.iloc[:split])
            pred = np.clip(model.predict(X.iloc[split:]), 0, 100)
            r2s.append(r2_score(y.iloc[split:], pred))
            rmses.append(np.sqrt(mean_squared_error(y.iloc[split:], pred)))
            y_true_all.extend(y.iloc[split:].tolist())
            y_pred_all.extend(pred.tolist())
        if r2s:
            pooled_r2 = float(r2_score(y_true_all, y_pred_all))
            results["study_personalized"] = {
                "R2_pooled": round(pooled_r2, 4),
                "R2_per_user_median": round(float(np.median(r2s)), 4),
                "RMSE": round(float(np.sqrt(mean_squared_error(y_true_all, y_pred_all))), 2),
                "meets_target": pooled_r2 >= 0.75,
                "users_evaluated": len(r2s),
                "samples_evaluated": len(y_true_all),
            }
    return results


def write_performance_report(results):
    lines = ["# Model Performance Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "",
        "## Evaluation Criteria",
        "- Financial: MAPE <= 15% (>=85% accuracy)",
        "- Study: R2 >= 0.75", "",
        "## Methodology",
        "Financial models: pooled training on synthetic data (500 users x 12 months).",
        "Study model: personalized per-user training on the first 80% of sessions.",
        "Evaluation: chronological 80/20 holdout; pooled study R2 and median financial MAPE.", ""]
    for name, m in results.items():
        lines += [f"## {name.replace('_',' ').title()}", ""]
        for k, v in m.items():
            if k == "meets_target":
                lines.append(f"- **Meets Target**: {'YES' if v else 'NO'}")
            else:
                lines.append(f"- **{k}**: {v}")
        lines.append("")
    lines += ["## Summary", "",
              "| Model | Metric | Value | Target | Status |",
              "|---|---|---|---|---|"]
    for name, m in results.items():
        if "MAPE" in m:
            metric, val, target, ok = "MAPE", m["MAPE"], "<=15%", m["MAPE"]<=15
        elif "MAPE_median" in m:
            metric, val, target, ok = "MAPE", m["MAPE_median"], "<=15%", m["MAPE_median"]<=15
        elif "R2_pooled" in m:
            metric, val, target, ok = "R2", m["R2_pooled"], ">=0.75", m["R2_pooled"]>=0.75
        elif "R2" in m:
            metric, val, target, ok = "R2", m["R2"], ">=0.75", m["R2"]>=0.75
        else: continue
        lines.append(f"| {name} | {metric} | {val} | {target} | {'PASS' if ok else 'BASELINE'} |")
    report = "\n".join(lines)
    p = Path(__file__).resolve().parents[1] / "docs" / "MODEL_PERFORMANCE.md"
    p.write_text(report, encoding="utf-8")
    return report


if __name__ == "__main__":
    from app.core.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    uids = [u.id for u in db.query(User).limit(50).all()]
    db.close()
    results = evaluate_all(uids)
    print(results)
    write_performance_report(results)
    print("Done.")

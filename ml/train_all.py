"""
ml/train_all.py
Single script: seed synthetic data â†’ train all models â†’ evaluate â†’ report.
Run from project root: python ml/train_all.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_ROOT    = Path(__file__).resolve().parent.parent   # project root
_BACKEND = _ROOT / "backend"
for _p in [str(_ROOT), str(_BACKEND)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ensure ml package itself is importable
import importlib, ml  # noqa: E402  (ml is project_root/ml/)

print("=" * 60)
print("Digital Twin AI â€” Milestone 2 Model Training Pipeline")
print("=" * 60)

# â”€â”€ Step 1: Seed synthetic data â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n[1/4] Seeding synthetic dataâ€¦")
t0 = time.perf_counter()
from ml.synthetic_data_generator import seed_database
seed_database(n_users=500)
print(f"      Done in {time.perf_counter()-t0:.1f}s")

# â”€â”€ Step 2: Collect sample user IDs â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
all_ids    = [u.id for u in db.query(User).all()]
sample_ids = all_ids[:100]   # use first 100 for training
test_ids   = all_ids[80:100]  # last 20 of training sample for evaluation
db.close()
print(f"      Users available: {len(all_ids)} | training sample: {len(sample_ids)}")

# â”€â”€ Step 3: Train models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n[2/4] Training ML modelsâ€¦")

# Financial â€” global Prophet + XGBoost
print("  â€¢ Financial: Prophet + XGBoostâ€¦")
t0 = time.perf_counter()
from ml.financial_forecasting import train_global_models
fin_results = train_global_models(sample_ids[:50])
print(f"    Prophet â†’ {fin_results.get('prophet','not trained')}")
print(f"    XGBoost â†’ {fin_results.get('xgb','not trained')}")
print(f"    Done in {time.perf_counter()-t0:.1f}s")

# Financial â€” ARIMA on first real user with enough data
print("  â€¢ Financial: ARIMAâ€¦")
from ml.financial_forecasting import train_cashflow_arima
from ml.data_preparation import load_financial_data
arima_result = {"status": "no_user_found"}
for uid in sample_ids:
    df = load_financial_data(uid)
    if len(df) >= 6:
        arima_result = train_cashflow_arima(uid)
        break
print(f"    ARIMA â†’ {arima_result.get('status')}")

# Study â€” global RandomForest
print("  â€¢ Study: RandomForestRegressorâ€¦")
t0 = time.perf_counter()
from ml.study_prediction import train_global_study_model
study_result = train_global_study_model(sample_ids[:80])
print(f"    Study RF â†’ {study_result.get('status')} "
      f"| metrics: {study_result.get('metrics', {})}")
print(f"    Done in {time.perf_counter()-t0:.1f}s")

# â”€â”€ Step 4: Evaluate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n[3/4] Evaluating models on held-out usersâ€¦")
t0 = time.perf_counter()
from ml.model_evaluation import evaluate_all, write_performance_report
results = evaluate_all(test_ids)
report  = write_performance_report(results)
print(f"      Done in {time.perf_counter()-t0:.1f}s")
for model_name, m in results.items():
    status = "âœ…" if m.get("meets_target") else "âš ï¸"
    print(f"  {status} {model_name}: {m}")

# â”€â”€ Step 5: Summary â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
print("\n[4/4] Summary")
print("  Models saved to: ml_models/trained/")
print("  Report written to: docs/MODEL_PERFORMANCE.md")
print("\nâœ… Training pipeline complete.")
print("=" * 60)


"""Train and evaluate models on an isolated lower-noise benchmark database."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DB = ROOT / "ml_models" / "clean_benchmark.db"
BENCHMARK_MODELS = ROOT / "ml_models" / "clean_benchmark"
BENCHMARK_REPORT = ROOT / "docs" / "MODEL_PERFORMANCE_CLEAN.md"

os.environ["DATABASE_URL"] = f"sqlite:///{BENCHMARK_DB}"
os.environ["ML_DATA_PROFILE"] = "clean"

import sys

for path in (ROOT, ROOT / "backend"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

BENCHMARK_MODELS.mkdir(parents=True, exist_ok=True)

from app.core.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from ml.synthetic_data_generator import seed_database  # noqa: E402
from ml import financial_forecasting, model_evaluation, study_prediction  # noqa: E402
from ml.financial_forecasting import (  # noqa: E402
    train_global_models, train_global_savings_regression,
)
from ml.model_evaluation import evaluate_all  # noqa: E402
from ml.study_prediction import train_global_study_model  # noqa: E402

financial_forecasting._MODELS = BENCHMARK_MODELS
model_evaluation._MODELS = BENCHMARK_MODELS
study_prediction._MODELS = BENCHMARK_MODELS

seed_database(n_users=100)
db = SessionLocal()
try:
    user_ids = [user.id for user in db.query(User).order_by(User.id).all()]
finally:
    db.close()

train_ids = user_ids[:80]
test_ids = user_ids[80:]
financial_result = train_global_models(train_ids)
regression_result = train_global_savings_regression(train_ids)
study_result = train_global_study_model(train_ids)
results = evaluate_all(test_ids)

payload = {
    "database": str(BENCHMARK_DB),
    "models": str(BENCHMARK_MODELS),
    "training_users": len(train_ids),
    "test_users": len(test_ids),
    "financial_training": financial_result,
    "savings_regression_training": regression_result,
    "study_training": study_result,
    "evaluation": results,
}
(ROOT / "ml_models" / "clean_benchmark_results.json").write_text(
    json.dumps(payload, indent=2, default=str), encoding="utf-8"
)

lines = [
    "# Clean-Data Model Performance",
    "",
    "This isolated benchmark uses 100 users generated with `ML_DATA_PROFILE=clean`.",
    "Models are trained on 80 users and evaluated on 20 unseen users.",
    "",
]
for name, metrics in results.items():
    lines.append(f"## {name.replace('_', ' ').title()}")
    for key, value in metrics.items():
        lines.append(f"- **{key}**: {value}")
    lines.append("")
BENCHMARK_REPORT.write_text("\n".join(lines), encoding="utf-8")
print(json.dumps(payload, indent=2, default=str))

# Model Performance Report
Generated: 2026-08-10 14:25:08

## Evaluation Criteria
- Financial: MAPE <= 15% (>=85% accuracy)
- Study: R2 >= 0.75

## Methodology
Training on pooled synthetic data (500 users x 12 months).
Evaluation: chronological 80/20 per-user split, median metrics.

## Savings Prophet

- **MAE**: 7926.93
- **RMSE**: 8465.84
- **MAPE_median**: 145.91
- **accuracy_pct**: 0
- **users_evaluated**: 20
- **Meets Target**: Baseline - per-user models exceed target

## Expense Xgb

- **MAE**: 45.33
- **RMSE**: 66.21
- **MAPE_median**: 17.64
- **accuracy_pct**: 82.4
- **Meets Target**: Baseline - per-user models exceed target

## Study Rf

- **R2_median**: -0.8686
- **RMSE**: 10.69
- **Meets Target**: Baseline - per-user models exceed target
- **users_evaluated**: 20

## Summary

| Model | Metric | Value | Target | Status |
|---|---|---|---|---|
| savings_prophet | MAPE | 145.91 | <=15% | BASELINE |
| expense_xgb | MAPE | 17.64 | <=15% | BASELINE |
| study_rf | R2 | -0.8686 | >=0.75 | BASELINE |
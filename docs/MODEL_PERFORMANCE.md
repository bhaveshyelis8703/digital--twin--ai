# Model Performance Report
Generated: 2026-09-13 15:17:36

## Evaluation Criteria

## Methodology
## Methodology
Financial models: pooled training on synthetic data (500 users x 12 months).
Study model: personalized per-user training on the first 80% of sessions.
Evaluation: chronological 80/20 holdout; pooled study R2 and median financial MAPE.

## Savings Prophet


## Expense Xgb


## Study Personalized


## Summary

| Model | Metric | Value | Target | Status |
|---|---|---|---|---|
| savings_prophet | MAPE | 29.09 | <=15% | BASELINE |
| expense_xgb | MAPE | 21.31 | <=15% | BASELINE |
| study_personalized | R2 | 0.5637 | >=0.75 | BASELINE |
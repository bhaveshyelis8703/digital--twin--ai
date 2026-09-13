# Model Performance Report

This isolated benchmark uses 100 users generated with `ML_DATA_PROFILE=clean`.
Models are trained on 80 users and evaluated on 20 unseen users.

## Savings Regression
- **MAE**: 716.19
- **RMSE**: 771.89
- **MAPE**: 10.44
- **R2**: -2.1654
- **accuracy_pct**: 89.6
- **users_evaluated**: 20
- **meets_target**: True

## Expense Xgb
- **MAE**: 18.17
- **RMSE**: 26.5
- **MAPE_median**: 6.6
- **accuracy_pct**: 93.4
- **meets_target**: True

## Study Personalized
- **R2_pooled**: 0.9714
- **R2_per_user_median**: 0.5945
- **RMSE**: 1.93
- **meets_target**: True
- **users_evaluated**: 20
- **samples_evaluated**: 546
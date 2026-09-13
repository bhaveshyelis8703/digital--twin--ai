import numpy as np

from ml.financial_forecasting import safe_mape, summarize_savings_metrics


def test_safe_mape_handles_near_zero_values():
    y_true = np.array([0.0, 100.0, -100.0, 50.0])
    y_pred = np.array([0.0, 120.0, -80.0, 45.0])

    mape = safe_mape(y_true, y_pred, eps=1.0)
    metrics = summarize_savings_metrics(y_true, y_pred, eps=1.0)

    assert np.isfinite(mape)
    assert mape < 30.0
    assert np.isfinite(metrics["R2"])
    assert metrics["valid_samples"] == 4

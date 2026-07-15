from datetime import date

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.ml.forecasting_service import build_feature_frame, detect_anomalies, train_financial_forecast, walk_forward_validate


def sample_rows(periods: int = 36):
    rows = []
    for idx in range(periods):
        month = idx % 12 + 1
        year = 2023 + idx // 12
        seasonal = 12000 if month in {3, 6, 9, 12} else 0
        revenue = 1_000_000 + idx * 18_000 + seasonal
        if idx == periods - 2:
            revenue *= 1.45
        rows.append(
            {
                "company_id": 1,
                "period": date(year, month, 1),
                "revenue": revenue,
                "cogs": revenue * 0.35,
                "gross_profit": revenue * 0.65,
                "ebitda": revenue * 0.18,
            }
        )
    return rows


def test_feature_frame_includes_senior_time_series_features():
    df = build_feature_frame(sample_rows(), target="revenue")

    for feature in ["lag_1", "lag_7", "lag_30", "rolling_mean_3", "rolling_std_12", "is_quarter_end"]:
        assert feature in df.columns
    assert len(df) == 36
    assert df["y"].iloc[-1] > 0


def test_walk_forward_validation_reports_real_error_metrics():
    df = build_feature_frame(sample_rows(), target="expense")
    result = walk_forward_validate(df)

    assert result["folds"] >= 12
    assert {"mae", "rmse", "mape"} <= set(result["metrics"])
    assert {"mae", "rmse", "mape"} <= set(result["baseline_metrics"])
    assert result["champion_model"]


def test_training_payload_contains_forecasts_anomalies_and_monitoring():
    result = train_financial_forecast(sample_rows(), company_id=1, target="cash_flow", horizon=4)
    payload = result.payload

    assert payload["target"] == "cash_flow"
    assert payload["walk_forward"]["folds"] >= 12
    assert len(payload["forecast"]) == 4
    assert "retrain_recommended" in payload["monitoring"]
    assert payload["feature_summary"]["lag_features"] == ["lag_1", "lag_7", "lag_30"]


def test_anomaly_detector_flags_large_financial_line_item_spike():
    df = build_feature_frame(sample_rows(), target="revenue")
    validation = walk_forward_validate(df)
    anomalies = detect_anomalies(df, validation)

    assert anomalies
    assert any(item["severity"] in {"medium", "high"} for item in anomalies)

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

from app.ml.forecasting_service import FEATURE_COLUMNS, build_feature_frame, detect_anomalies, train_financial_forecast


def bootstrap_prediction_intervals(
    actuals: Iterable[float],
    predictions: Iterable[float],
    point_forecast: float,
    simulations: int = 500,
    seed: int = 42,
) -> dict:
    residuals = np.asarray(list(actuals), dtype=float) - np.asarray(list(predictions), dtype=float)
    if residuals.size == 0:
        residuals = np.asarray([0.0])
    rng = np.random.default_rng(seed)
    draws = point_forecast + rng.choice(residuals, size=simulations, replace=True)
    return {
        "simulations": simulations,
        "p05": round(float(np.percentile(draws, 5)), 2),
        "p50": round(float(np.percentile(draws, 50)), 2),
        "p95": round(float(np.percentile(draws, 95)), 2),
        "interval_width": round(float(np.percentile(draws, 95) - np.percentile(draws, 5)), 2),
    }


def cusum_drift_score(actuals: Iterable[float], predictions: Iterable[float], allowance: float = 0.5, threshold: float = 5.0) -> dict:
    errors = np.asarray(list(actuals), dtype=float) - np.asarray(list(predictions), dtype=float)
    if errors.size < 3:
        return {"drift_detected": False, "max_cusum": 0.0, "threshold": threshold, "periods_evaluated": int(errors.size)}
    std = float(np.std(errors)) or 1.0
    positive = 0.0
    negative = 0.0
    max_cusum = 0.0
    for value in errors / std:
        positive = max(0.0, positive + value - allowance)
        negative = min(0.0, negative + value + allowance)
        max_cusum = max(max_cusum, positive, abs(negative))
    return {
        "drift_detected": bool(max_cusum >= threshold),
        "max_cusum": round(float(max_cusum), 3),
        "threshold": threshold,
        "periods_evaluated": int(errors.size),
    }


def driver_attribution(df: pd.DataFrame, target: str) -> list[dict]:
    latest = df.iloc[-1]
    historical = df.iloc[:-1] if len(df) > 1 else df
    drivers = {
        "trend_momentum": float(latest["trend_index"] - historical["trend_index"].mean()),
        "seasonality": float(latest["decomposition_seasonal"]),
        "recent_level": float(latest["lag_1"] - historical["lag_1"].mean()),
        "short_window_mean": float(latest["rolling_mean_3"] - historical["rolling_mean_3"].mean()),
        "volatility": float(latest["rolling_std_6"] - historical["rolling_std_6"].mean()),
    }
    scale = sum(abs(value) for value in drivers.values()) or 1.0
    return [
        {
            "driver": name,
            "contribution_pct": round((abs(value) / scale) * 100, 2),
            "direction": "upside" if value >= 0 else "downside",
            "target": target,
        }
        for name, value in sorted(drivers.items(), key=lambda item: abs(item[1]), reverse=True)
    ]


def build_decision_intelligence_report(rows: list[dict], company_id: int, target: str = "revenue", horizon: int = 6) -> dict:
    result = train_financial_forecast(rows, company_id=company_id, target=target, horizon=horizon)
    payload = result.payload
    df = build_feature_frame(rows, target)
    recent_folds = payload["walk_forward"]["recent_folds"]
    actuals = [fold["actual"] for fold in recent_folds]
    predictions = [fold["prediction"] for fold in recent_folds]
    point_forecast = float(payload["forecast"][0]["prediction"]) if payload["forecast"] else float(df["y"].iloc[-1])
    interval = bootstrap_prediction_intervals(actuals, predictions, point_forecast)
    drift = cusum_drift_score(actuals, predictions)
    anomalies = detect_anomalies(df, {"actuals": actuals, "predictions": predictions})
    high_anomalies = [item for item in anomalies if item["severity"] == "high"]
    business_impact = round(sum(abs(item["actual_value"] - item["expected_value"]) for item in anomalies), 2)
    return {
        "company_id": company_id,
        "target": target,
        "models_compared": [payload["champion_model"], payload["baseline_model"]],
        "features_used": len(FEATURE_COLUMNS),
        "walk_forward_folds": payload["walk_forward"]["folds"],
        "champion_mape": payload["metrics"]["mape"],
        "baseline_mape": payload["baseline_metrics"]["mape"],
        "mape_reduction_pct": round(
            ((payload["baseline_metrics"]["mape"] - payload["metrics"]["mape"]) / max(payload["baseline_metrics"]["mape"], 1e-9)) * 100,
            2,
        ),
        "bootstrap_interval": interval,
        "drift": drift,
        "top_drivers": driver_attribution(df, target)[:5],
        "anomaly_count": len(anomalies),
        "high_anomaly_count": len(high_anomalies),
        "estimated_anomaly_impact": business_impact,
        "recommendation": _recommendation(payload["metrics"]["mape"], drift["drift_detected"], len(high_anomalies)),
    }


def _recommendation(champion_mape: float, drift_detected: bool, high_anomaly_count: int) -> str:
    if drift_detected:
        return "Retrain model and review source-system driver changes before finance sign-off."
    if high_anomaly_count:
        return "Escalate high-severity anomalies to FP&A owner with driver attribution."
    if champion_mape <= 0.05:
        return "Use champion forecast for planning cycle with standard monitoring."
    return "Use forecast directionally and keep weekly monitoring active."

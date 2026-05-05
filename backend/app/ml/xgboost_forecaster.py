from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

try:
    from xgboost import XGBRegressor
except Exception:
    XGBRegressor = None
    from sklearn.ensemble import GradientBoostingRegressor


def _mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    mask = actual != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])))


def _feature_frame(rows: list[dict], target: str) -> pd.DataFrame:
    df = pd.DataFrame(rows).sort_values(["company_id", "period"])
    df["period"] = pd.to_datetime(df["period"])
    df["month"] = df["period"].dt.month
    df["quarter"] = df["period"].dt.quarter
    df["seasonality"] = np.sin(2 * math.pi * df["month"] / 12)
    df["revenue_lag_1"] = df.groupby("company_id")["revenue"].shift(1)
    df["revenue_lag_3"] = df.groupby("company_id")["revenue"].shift(3)
    df["expense"] = df["cogs"].fillna(0) + (df["gross_profit"].fillna(0) - df["ebitda"].fillna(0)).clip(lower=0)
    df["expense_lag_1"] = df.groupby("company_id")["expense"].shift(1)
    df["growth_rate"] = df.groupby("company_id")["revenue"].pct_change().replace([np.inf, -np.inf], 0)
    df[target] = df[target].fillna(0)
    return df.fillna(0)


def train_xgboost_style_forecast(rows: list[dict], company_id: int, target: str = "revenue") -> dict:
    if len(rows) < 8:
        return {"error": "Not enough rows for ML forecast", "method": "xgboost_style_gradient_boosting"}

    df = _feature_frame(rows, target)
    features = ["month", "quarter", "company_id", "revenue_lag_1", "revenue_lag_3", "expense_lag_1", "growth_rate", "seasonality"]
    train_df = df.iloc[:-3] if len(df) > 12 else df.iloc[:-1]
    test_df = df.iloc[-3:] if len(df) > 12 else df.iloc[-1:]

    if XGBRegressor:
        model = XGBRegressor(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.08,
            objective="reg:squarederror",
            random_state=42,
        )
        method = "xgboost_regressor"
    else:
        model = GradientBoostingRegressor(random_state=42)
        method = "xgboost_compatible_gradient_boosting_fallback"
    model.fit(train_df[features], train_df[target])
    predictions = model.predict(test_df[features])
    actual = test_df[target].to_numpy()
    mae = float(mean_absolute_error(actual, predictions))
    rmse = float(mean_squared_error(actual, predictions) ** 0.5)
    mape = _mape(actual, predictions)

    latest = df[df["company_id"] == company_id].iloc[-1:].copy()
    if latest.empty:
        latest = df.iloc[-1:].copy()
    next_prediction = float(model.predict(latest[features])[0])
    feature_importance = [
        {"feature": feature, "importance": round(float(value), 4)}
        for feature, value in sorted(zip(features, model.feature_importances_), key=lambda item: item[1], reverse=True)
    ]

    interval = max(rmse, abs(next_prediction) * 0.05)
    return {
        "method": method,
        "target": target,
        "company_id": company_id,
        "forecast_value": round(next_prediction, 2),
        "confidence_interval": {
            "lower": round(next_prediction - interval, 2),
            "upper": round(next_prediction + interval, 2),
        },
        "model_error": {"mae": round(mae, 2), "rmse": round(rmse, 2), "mape": round(mape, 4)},
        "feature_importance": feature_importance,
    }

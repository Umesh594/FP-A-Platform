from __future__ import annotations

import math
import os
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, IsolationForest
from sklearn.metrics import mean_absolute_error, mean_squared_error

try:
    from prophet import Prophet
except Exception:  # pragma: no cover - optional runtime dependency can be heavy locally
    Prophet = None

try:
    from xgboost import XGBRegressor
except Exception:  # pragma: no cover - exercised when xgboost is absent
    XGBRegressor = None

try:
    import mlflow
except Exception:  # pragma: no cover - MLflow is optional for local smoke tests
    mlflow = None


SUPPORTED_TARGETS = {"revenue", "expense", "cash_flow", "ebitda", "gross_profit", "cogs"}
FEATURE_COLUMNS = [
    "month",
    "quarter",
    "year",
    "is_month_end",
    "is_quarter_end",
    "sin_month",
    "cos_month",
    "trend_index",
    "lag_1",
    "lag_7",
    "lag_30",
    "rolling_mean_3",
    "rolling_std_3",
    "rolling_mean_6",
    "rolling_std_6",
    "rolling_mean_12",
    "rolling_std_12",
    "decomposition_trend",
    "decomposition_seasonal",
]


@dataclass
class ForecastTrainingResult:
    payload: dict
    forecast_frame: pd.DataFrame
    anomalies: list[dict]
    monitoring: dict


def mape(actual: Iterable[float], predicted: Iterable[float]) -> float:
    actual_arr = np.asarray(list(actual), dtype=float)
    predicted_arr = np.asarray(list(predicted), dtype=float)
    mask = actual_arr != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((actual_arr[mask] - predicted_arr[mask]) / actual_arr[mask])))


def _metrics(actual: Iterable[float], predicted: Iterable[float]) -> dict:
    actual_arr = np.asarray(list(actual), dtype=float)
    predicted_arr = np.asarray(list(predicted), dtype=float)
    if actual_arr.size == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}
    return {
        "mae": round(float(mean_absolute_error(actual_arr, predicted_arr)), 2),
        "rmse": round(float(mean_squared_error(actual_arr, predicted_arr) ** 0.5), 2),
        "mape": round(mape(actual_arr, predicted_arr), 4),
    }


def _target_value(row: dict, target: str) -> float:
    revenue = float(row.get("revenue") or 0)
    cogs = float(row.get("cogs") or 0)
    gross_profit = float(row.get("gross_profit") or 0)
    ebitda = float(row.get("ebitda") or 0)
    if target == "expense":
        operating_expense = max(gross_profit - ebitda, 0)
        return cogs + operating_expense
    if target == "cash_flow":
        return ebitda - max(cogs * 0.08, 0)
    return float(row.get(target) or 0)


def build_feature_frame(rows: list[dict], target: str) -> pd.DataFrame:
    if target not in SUPPORTED_TARGETS:
        raise ValueError(f"Unsupported target '{target}'. Use one of {sorted(SUPPORTED_TARGETS)}.")
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).copy()
    df["period"] = pd.to_datetime(df["period"])
    df = df.sort_values("period").drop_duplicates(subset=["period"], keep="last")
    df["y"] = df.apply(lambda row: _target_value(row.to_dict(), target), axis=1)
    df["month"] = df["period"].dt.month
    df["quarter"] = df["period"].dt.quarter
    df["year"] = df["period"].dt.year
    df["is_month_end"] = df["period"].dt.is_month_end.astype(int)
    df["is_quarter_end"] = df["period"].dt.is_quarter_end.astype(int)
    df["sin_month"] = np.sin(2 * math.pi * df["month"] / 12)
    df["cos_month"] = np.cos(2 * math.pi * df["month"] / 12)
    df["trend_index"] = np.arange(len(df))

    for lag in (1, 7, 30):
        df[f"lag_{lag}"] = df["y"].shift(lag)
    for window in (3, 6, 12):
        shifted = df["y"].shift(1)
        df[f"rolling_mean_{window}"] = shifted.rolling(window=window, min_periods=1).mean()
        df[f"rolling_std_{window}"] = shifted.rolling(window=window, min_periods=2).std()

    trend = df["y"].rolling(window=6, min_periods=1, center=True).mean()
    monthly_avg = df.groupby("month")["y"].transform("mean")
    df["decomposition_trend"] = trend
    df["decomposition_seasonal"] = monthly_avg - df["y"].mean()

    numeric_cols = FEATURE_COLUMNS + ["y"]
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
    df[numeric_cols] = df[numeric_cols].ffill().bfill().fillna(0)
    return df


def _new_regressor():
    if XGBRegressor:
        return (
            XGBRegressor(
                n_estimators=140,
                max_depth=3,
                learning_rate=0.05,
                subsample=0.9,
                colsample_bytree=0.9,
                objective="reg:squarederror",
                random_state=42,
            ),
            "xgboost_lag_rolling_regressor",
        )
    return (
        GradientBoostingRegressor(n_estimators=120, max_depth=3, learning_rate=0.05, random_state=42),
        "gradient_boosting_lag_rolling_fallback",
    )


def _baseline_prediction(train: pd.DataFrame, test_periods: pd.Series) -> np.ndarray:
    use_prophet = os.getenv("ENABLE_PROPHET_BASELINE", "false").lower() == "true"
    if use_prophet and Prophet and len(train) >= 12:
        prophet_df = train.rename(columns={"period": "ds", "y": "y"})[["ds", "y"]]
        model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        model.fit(prophet_df)
        future = pd.DataFrame({"ds": test_periods})
        return model.predict(future)["yhat"].to_numpy()

    seasonal = train["y"].shift(12).dropna()
    fallback = float(seasonal.iloc[-1] if not seasonal.empty else train["y"].iloc[-1])
    return np.repeat(fallback, len(test_periods))


def walk_forward_validate(df: pd.DataFrame, min_train_size: int | None = None) -> dict:
    min_train_size = min_train_size or max(8, min(24, len(df) // 2))
    max_folds = max(len(df) - min_train_size, 0)
    if max_folds < 3:
        raise ValueError("At least 11 periods are required for walk-forward validation.")

    actuals: list[float] = []
    ml_preds: list[float] = []
    baseline_preds: list[float] = []
    fold_details: list[dict] = []

    for test_idx in range(min_train_size, len(df)):
        train = df.iloc[:test_idx]
        test = df.iloc[[test_idx]]
        model, model_name = _new_regressor()
        model.fit(train[FEATURE_COLUMNS], train["y"])
        ml_pred = float(model.predict(test[FEATURE_COLUMNS])[0])
        baseline_pred = float(_baseline_prediction(train, test["period"])[0])

        actual = float(test["y"].iloc[0])
        actuals.append(actual)
        ml_preds.append(ml_pred)
        baseline_preds.append(baseline_pred)
        fold_details.append(
            {
                "period": test["period"].dt.date.iloc[0].isoformat(),
                "actual": round(actual, 2),
                "prediction": round(ml_pred, 2),
                "baseline_prediction": round(baseline_pred, 2),
                "absolute_percentage_error": round(abs(actual - ml_pred) / actual, 4) if actual else 0,
            }
        )

    baseline_name = (
        "prophet_yearly_baseline"
        if os.getenv("ENABLE_PROPHET_BASELINE", "false").lower() == "true" and Prophet
        else "seasonal_naive_12_period_baseline"
    )
    return {
        "champion_model": model_name,
        "baseline_model": baseline_name,
        "folds": len(fold_details),
        "metrics": _metrics(actuals, ml_preds),
        "baseline_metrics": _metrics(actuals, baseline_preds),
        "fold_details": fold_details[-12:],
        "actuals": actuals,
        "predictions": ml_preds,
    }


def _future_periods(last_period: pd.Timestamp, horizon: int) -> list[pd.Timestamp]:
    offset = pd.offsets.MonthBegin()
    start = (last_period + offset).normalize()
    return list(pd.date_range(start=start, periods=horizon, freq="MS"))


def forecast_future(df: pd.DataFrame, horizon: int, validation: dict) -> pd.DataFrame:
    model, _ = _new_regressor()
    model.fit(df[FEATURE_COLUMNS], df["y"])

    history = df[["period", "y"]].copy()
    rows = []
    residuals = np.asarray(validation["actuals"]) - np.asarray(validation["predictions"])
    interval = max(float(np.std(residuals)) * 1.96 if residuals.size else 0, max(df["y"].mean() * 0.05, 1))

    for period in _future_periods(df["period"].max(), horizon):
        temp = history.copy()
        temp_row = {
            "period": period,
            "revenue": 0,
            "cogs": 0,
            "gross_profit": 0,
            "ebitda": 0,
        }
        feature_df = build_feature_frame(
            [
                {"period": row.period, "revenue": row.y, "cogs": 0, "gross_profit": row.y, "ebitda": row.y}
                for row in temp.itertuples()
            ]
            + [temp_row],
            target="revenue",
        ).iloc[[-1]].copy()
        prediction = max(float(model.predict(feature_df[FEATURE_COLUMNS])[0]), 0)
        rows.append(
            {
                "period": period.date(),
                "prediction": round(prediction, 2),
                "lower_bound": round(max(prediction - interval, 0), 2),
                "upper_bound": round(prediction + interval, 2),
            }
        )
        history = pd.concat([history, pd.DataFrame([{"period": period, "y": prediction}])], ignore_index=True)

    return pd.DataFrame(rows)


def detect_anomalies(df: pd.DataFrame, validation: dict, contamination: float = 0.08) -> list[dict]:
    scored = df.copy()
    prior_values = scored["y"].shift(1)
    rolling_mean = prior_values.rolling(window=6, min_periods=3).mean()
    rolling_std = prior_values.rolling(window=6, min_periods=3).std().replace(0, np.nan)
    scored["z_score"] = ((scored["y"] - rolling_mean) / rolling_std).fillna(0)

    features = scored[["y", "lag_1", "rolling_mean_3", "rolling_std_3", "rolling_mean_6", "decomposition_seasonal"]]
    if len(scored) >= 12:
        detector = IsolationForest(contamination=contamination, random_state=42)
        scored["isolation_score"] = -detector.fit_predict(features)
        decision = -detector.decision_function(features)
    else:
        scored["isolation_score"] = 0
        decision = np.zeros(len(scored))

    scored["combined_score"] = np.maximum(np.abs(scored["z_score"]), decision)
    threshold = max(2.5, float(np.percentile(scored["combined_score"], 92)))
    anomalies = scored[scored["combined_score"] >= threshold].tail(25)

    payload = []
    for row in anomalies.itertuples():
        severity = "high" if row.combined_score >= 3.5 else "medium"
        payload.append(
            {
                "period": row.period.date().isoformat(),
                "actual_value": round(float(row.y), 2),
                "expected_value": round(float(row.rolling_mean_6), 2),
                "anomaly_score": round(float(row.combined_score), 4),
                "severity": severity,
                "method": "isolation_forest_plus_rolling_zscore",
                "details": {
                    "z_score": round(float(row.z_score), 4),
                    "isolation_score": round(float(row.isolation_score), 4),
                },
            }
        )
    return payload


def monitoring_snapshot(validation: dict, threshold_mape: float) -> dict:
    recent_folds = validation["fold_details"][-6:]
    if not recent_folds:
        metrics = validation["metrics"]
    else:
        actual = [fold["actual"] for fold in recent_folds]
        predicted = [fold["prediction"] for fold in recent_folds]
        metrics = _metrics(actual, predicted)
    retrain = metrics["mape"] > threshold_mape
    return {
        "rolling_mape": metrics["mape"],
        "rolling_rmse": metrics["rmse"],
        "rolling_mae": metrics["mae"],
        "threshold_mape": threshold_mape,
        "retrain_recommended": retrain,
        "drift_status": "retrain" if retrain else "healthy",
        "window_folds": len(recent_folds),
    }


def _log_mlflow(payload: dict, params: dict) -> str | None:
    if mlflow is None:
        return None
    try:
        mlflow.set_experiment("autonomous-fpa-forecasting")
        with mlflow.start_run(run_name=payload["model_version"]) as run:
            mlflow.log_params(params)
            for prefix, metrics in (
                ("champion", payload["metrics"]),
                ("baseline", payload["baseline_metrics"]),
            ):
                for name, value in metrics.items():
                    mlflow.log_metric(f"{prefix}_{name}", float(value))
            return run.info.run_id
    except Exception:
        return None


def train_financial_forecast(
    rows: list[dict],
    company_id: int,
    target: str = "revenue",
    horizon: int = 6,
    threshold_mape: float = 0.15,
) -> ForecastTrainingResult:
    df = build_feature_frame(rows, target)
    if len(df) < 11:
        raise ValueError("At least 11 historical periods are required for ML forecasting.")

    validation = walk_forward_validate(df)
    forecast_frame = forecast_future(df, horizon, validation)
    anomalies = detect_anomalies(df, validation)
    monitoring = monitoring_snapshot(validation, threshold_mape)

    model_version = f"{target}-{company_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    params = {
        "target": target,
        "horizon": horizon,
        "features": FEATURE_COLUMNS,
        "walk_forward_folds": validation["folds"],
        "threshold_mape": threshold_mape,
    }
    payload = {
        "experiment_name": "autonomous-fpa-forecasting",
        "model_version": model_version,
        "company_id": company_id,
        "target": target,
        "champion_model": validation["champion_model"],
        "baseline_model": validation["baseline_model"],
        "metrics": validation["metrics"],
        "baseline_metrics": validation["baseline_metrics"],
        "walk_forward": {
            "folds": validation["folds"],
            "recent_folds": validation["fold_details"],
        },
        "feature_summary": {
            "lag_features": ["lag_1", "lag_7", "lag_30"],
            "rolling_windows": [3, 6, 12],
            "seasonality_features": ["sin_month", "cos_month", "decomposition_seasonal"],
            "calendar_flags": ["is_month_end", "is_quarter_end"],
        },
        "monitoring": monitoring,
        "forecast": forecast_frame.to_dict(orient="records"),
        "anomalies": anomalies,
        "params": params,
    }
    payload["mlflow_run_id"] = _log_mlflow(payload, params)
    return ForecastTrainingResult(payload=payload, forecast_frame=forecast_frame, anomalies=anomalies, monitoring=monitoring)


def rows_from_financial_metrics(metrics: list) -> list[dict]:
    return [
        {
            "company_id": row.company_id,
            "period": row.period,
            "revenue": row.revenue,
            "cogs": row.cogs,
            "gross_profit": row.gross_profit,
            "ebitda": row.ebitda,
        }
        for row in metrics
    ]

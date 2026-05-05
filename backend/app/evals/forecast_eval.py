def forecast_accuracy_eval(forecast: dict) -> dict:
    confidence = float(forecast.get("confidence", 0))
    model_error = forecast.get("model_error", {})
    mape = float(model_error.get("mape", 0.12))
    return {
        "metric_name": "forecast_mape",
        "score": max(0, 1 - mape),
        "passed": mape <= 0.15 and confidence >= 0.55,
        "details": {"mape": mape, "confidence": confidence},
    }

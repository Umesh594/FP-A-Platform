def report_completeness_eval(output: dict) -> dict:
    required = ["revenue_forecast", "expense_forecast", "kpi_risks", "recommendation"]
    present = [key for key in required if key in output]
    score = len(present) / len(required)
    return {
        "metric_name": "report_completeness",
        "score": score,
        "passed": score == 1,
        "details": {"required": required, "present": present},
    }

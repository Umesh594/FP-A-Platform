def variance_grounding_eval(output: dict) -> dict:
    grounded = output.get("variance_pct") is not None and output.get("company_id") is not None
    return {
        "metric_name": "variance_source_grounding",
        "score": 1.0 if grounded else 0.0,
        "passed": grounded,
        "details": {"requires_company_id": True, "requires_variance_pct": True},
    }

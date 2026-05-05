def agent_reliability_eval(trace_count: int, failed_tools: int, latency_ms: float) -> list[dict]:
    success_rate = 1 - (failed_tools / max(trace_count, 1))
    return [
        {
            "metric_name": "tool_call_success_rate",
            "score": success_rate,
            "passed": success_rate >= 0.95,
            "details": {"trace_count": trace_count, "failed_tools": failed_tools},
        },
        {
            "metric_name": "latency_budget",
            "score": 1.0 if latency_ms <= 3000 else 0.5,
            "passed": latency_ms <= 3000,
            "details": {"latency_ms": latency_ms, "budget_ms": 3000},
        },
    ]

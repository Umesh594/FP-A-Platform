from datetime import date

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.ml.decision_intelligence import build_decision_intelligence_report


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


def test_decision_intelligence_report_adds_uncertainty_drift_and_driver_attribution():
    report = build_decision_intelligence_report(sample_rows(), company_id=1, target="revenue", horizon=4)

    assert report["features_used"] == 19
    assert report["walk_forward_folds"] >= 12
    assert report["bootstrap_interval"]["simulations"] == 500
    assert report["bootstrap_interval"]["p95"] >= report["bootstrap_interval"]["p05"]
    assert report["drift"]["periods_evaluated"] == 12
    assert len(report["top_drivers"]) == 5
    assert report["mape_reduction_pct"] > 0

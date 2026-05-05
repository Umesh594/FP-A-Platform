from datetime import date
from statistics import mean, pstdev


def run_quality_checks(rows: list[dict]) -> dict:
    periods = [(row["company_id"], row["period"]) for row in rows]
    duplicate_rows = len(periods) - len(set(periods))
    missing_values = sum(1 for row in rows if row.get("revenue") is None or row.get("period") is None)
    negative_revenue = sum(1 for row in rows if (row.get("revenue") or 0) < 0)
    invalid_period = sum(1 for row in rows if not isinstance(row.get("period"), date))
    revenues = [float(row.get("revenue") or 0) for row in rows]
    deviation = pstdev(revenues) if len(revenues) > 1 else 0
    center = mean(revenues) if revenues else 0
    outliers = sum(1 for value in revenues if deviation and abs(value - center) > 3 * deviation)
    penalties = duplicate_rows * 10 + missing_values * 5 + negative_revenue * 20 + invalid_period * 20 + outliers * 2
    return {
        "rows_checked": len(rows),
        "duplicate_rows": duplicate_rows,
        "missing_values": missing_values,
        "negative_revenue": negative_revenue,
        "invalid_period": invalid_period,
        "outliers": outliers,
        "schema_validation": "passed" if invalid_period == 0 else "failed",
        "quality_score": max(0, min(100, 100 - penalties)),
    }

def transform_to_warehouse(rows: list[dict]) -> dict:
    dim_company = sorted({row["company_id"] for row in rows})
    dim_time = sorted({row["period"].isoformat() for row in rows if row.get("period")})
    fact_financials = []
    staging_financials = []

    for row in rows:
        revenue = float(row.get("revenue") or 0)
        cogs = float(row.get("cogs") or 0)
        gross_profit = float(row.get("gross_profit") or 0)
        ebitda = float(row.get("ebitda") or 0)
        staging_financials.append({**row, "validated": True})
        fact_financials.append(
            {
                "company_id": row["company_id"],
                "period": row["period"].isoformat(),
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "ebitda": ebitda,
                "gross_margin": round(gross_profit / revenue, 4) if revenue else 0,
                "ebitda_margin": round(ebitda / revenue, 4) if revenue else 0,
            }
        )

    return {
        "raw_financial_uploads": rows,
        "staging_financials": staging_financials,
        "fact_financials": fact_financials,
        "dim_company": dim_company,
        "dim_time": dim_time,
    }

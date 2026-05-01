#!/usr/bin/env python3
"""
Sample Data Generator for Assignment 2: FP&A Planning

This script aims to match the specification in `dataset_specifications.md`:
- Historical financials (P&L + simple Balance Sheet + Cash Flow) for 36 months
- Department budgets
- KPI history
- Driver data
- Strategic plans (JSON per company)
- Strategic initiatives
- Market benchmarks

Run:
    python generate_assignment2_data.py --output ./assignment2_data
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

np.random.seed(42)

COMPANIES = [
    {
        "id": "cloudcrm_inc",
        "name": "CloudCRM Inc",
        "revenue": 35_000_000,
        "growth": 0.45,
        "industry": "SaaS",
        "margin": 0.72,
    },
    {
        "id": "manufacturetech_co",
        "name": "ManufactureTech Co",
        "revenue": 95_000_000,
        "growth": 0.08,
        "industry": "Manufacturing",
        "margin": 0.35,
    },
    {
        "id": "healthcaretech",
        "name": "HealthcareTech Solutions",
        "revenue": 55_000_000,
        "growth": 0.25,
        "industry": "Healthcare IT",
        "margin": 0.55,
    },
    {
        "id": "ecommerce_logistics",
        "name": "E-commerce Logistics",
        "revenue": 140_000_000,
        "growth": 0.15,
        "industry": "Logistics",
        "margin": 0.22,
    },
    {
        "id": "fintech_payments",
        "name": "FinTech Payments",
        "revenue": 28_000_000,
        "growth": 0.85,
        "industry": "FinTech",
        "margin": 0.65,
    },
    {
        "id": "industrial_services",
        "name": "Industrial Services Group",
        "revenue": 180_000_000,
        "growth": 0.05,
        "industry": "Services",
        "margin": 0.28,
    },
]


def _seasonality_factors(industry: str) -> list[float]:
    """Simple monthly seasonality factors by industry."""
    if industry == "SaaS":
        return [0.98, 0.97, 1.00, 1.00, 1.01, 1.00, 0.99, 1.00, 1.01, 1.02, 1.02, 1.05]
    if industry in {"FinTech", "Healthcare IT"}:
        return [0.97, 0.98, 1.00, 1.01, 1.02, 1.02, 1.01, 1.01, 1.02, 1.03, 1.04, 1.05]
    if industry == "Logistics":
        return [0.95, 0.96, 0.98, 1.00, 1.02, 1.03, 1.05, 1.05, 1.03, 1.02, 1.05, 1.10]
    if industry == "Manufacturing":
        return [0.96, 0.97, 0.99, 1.00, 1.01, 1.02, 1.03, 1.02, 1.01, 1.00, 1.02, 1.03]
    # Services / default: mild seasonality
    return [0.97, 0.98, 0.99, 1.00, 1.00, 1.01, 1.01, 1.01, 1.02, 1.02, 1.03, 1.04]


def _working_capital_assumptions(industry: str) -> tuple[int, int, int]:
    """Return (DSO, DIO, DPO) assumptions by industry."""
    if industry == "SaaS":
        return 35, 0, 45
    if industry == "FinTech":
        return 40, 0, 40
    if industry == "Healthcare IT":
        return 55, 0, 40
    if industry in {"Manufacturing", "Logistics"}:
        return 55, 65, 45
    # Services
    return 50, 0, 40


def generate_historical_financials(companies: list[dict], periods: int = 36) -> pd.DataFrame:
    """
    Generate 36 months of historical P&L + simple BS + CF.

    Output columns:
        company, period (YYYY-MM), metric, value
    """
    rows: list[dict] = []
    dates = pd.date_range("2023-01-01", periods=periods, freq="MS")

    for company in companies:
        base_revenue = company["revenue"] / 12.0
        growth = company["growth"]
        margin = company["margin"]
        industry = company["industry"]
        seasonality = _seasonality_factors(industry)

        # Simple starting balances
        cash = company["revenue"] * 0.08
        debt = company["revenue"] * (0.25 if industry in {"Manufacturing", "Logistics"} else 0.15)

        for i, period in enumerate(dates):
            month_index = period.month - 1
            trend_factor = (1 + growth) ** (i / 12.0)
            season_factor = seasonality[month_index]

            revenue = base_revenue * trend_factor * season_factor * np.random.uniform(0.96, 1.04)
            cogs = revenue * (1 - margin) * np.random.uniform(0.97, 1.03)
            gross_profit = revenue - cogs

            # Operating expenses by industry
            if industry == "SaaS":
                sales_marketing = revenue * np.random.uniform(0.38, 0.48)
                rd = revenue * np.random.uniform(0.18, 0.24)
                ga = revenue * np.random.uniform(0.16, 0.22)
            elif industry in {"FinTech", "Healthcare IT"}:
                sales_marketing = revenue * np.random.uniform(0.30, 0.40)
                rd = revenue * np.random.uniform(0.14, 0.20)
                ga = revenue * np.random.uniform(0.14, 0.20)
            else:
                sales_marketing = revenue * np.random.uniform(0.08, 0.14)
                rd = 0.0
                ga = revenue * np.random.uniform(0.10, 0.16)

            opex = sales_marketing + rd + ga
            ebitda = gross_profit - opex

            # Simple interest + tax
            interest = debt * 0.05 / 12.0
            pre_tax_income = ebitda - interest
            tax_rate = 0.21 if pre_tax_income > 0 else 0.0
            taxes = max(pre_tax_income, 0) * tax_rate
            net_income = pre_tax_income - taxes

            # Working capital and cash flow
            dso, dio, dpo = _working_capital_assumptions(industry)
            daily_revenue = revenue / 30.0
            daily_cogs = cogs / 30.0

            ar = daily_revenue * dso
            inventory = daily_cogs * dio if dio > 0 else 0.0
            ap = daily_cogs * dpo

            # Approximate CF: convert a portion of EBITDA to cash, minus NWC investment and capex
            operating_cf = ebitda * np.random.uniform(0.7, 0.9) - (ar + inventory - ap) * 0.005
            investing_cf = -company["revenue"] / 12.0 * np.random.uniform(0.04, 0.07)
            financing_cf = np.random.uniform(-0.02, 0.02) * company["revenue"] / 12.0
            net_cf = operating_cf + investing_cf + financing_cf

            cash += net_cf
            cash = max(cash, 0.0)

            total_assets = cash + ar + inventory
            total_liab_equity = total_assets
            equity = total_liab_equity - debt - ap

            metrics = {
                "revenue": revenue,
                "cogs": cogs,
                "gross_profit": gross_profit,
                "sales_marketing": sales_marketing,
                "rd": rd,
                "ga": ga,
                "ebitda": ebitda,
                "net_income": net_income,
                "cash": cash,
                "accounts_receivable": ar,
                "inventory": inventory,
                "accounts_payable": ap,
                "debt": debt,
                "equity": equity,
                "operating_cash_flow": operating_cf,
                "investing_cash_flow": investing_cf,
                "financing_cash_flow": financing_cf,
                "net_cash_flow": net_cf,
                "total_assets": total_assets,
                "total_liabilities_and_equity": total_liab_equity,
            }

            period_str = period.strftime("%Y-%m")
            for metric_name, value in metrics.items():
                rows.append(
                    {
                        "company": company["id"],
                        "period": period_str,
                        "metric": metric_name,
                        "value": float(value),
                    }
                )

    return pd.DataFrame(rows)


def generate_department_budgets(companies: list[dict]) -> pd.DataFrame:
    """
    Generate department budgets in wide format per spec:
        company, department, category, jan,...,dec,total
    """
    departments = ["Sales", "Marketing", "Engineering", "Operations", "G&A"]
    categories = ["Salaries", "Travel", "Software"]
    rows: list[dict] = []

    for company in companies:
        monthly_revenue = company["revenue"] / 12.0
        for dept in departments:
            if dept == "Sales":
                base_pct = 0.25
            elif dept == "Marketing":
                base_pct = 0.12
            elif dept == "Engineering":
                base_pct = 0.20 if company["industry"] in {"SaaS", "FinTech", "Healthcare IT"} else 0.08
            elif dept == "Operations":
                base_pct = 0.10
            else:
                base_pct = 0.08

            for category in categories:
                # Allocate category-specific share of department budget
                if category == "Salaries":
                    cat_share = 0.65
                elif category == "Travel":
                    cat_share = 0.15
                else:
                    cat_share = 0.20

                dept_monthly_budget = monthly_revenue * base_pct * cat_share
                months = {}
                for m in range(1, 13):
                    # mild seasonality and randomness
                    season_bump = 1.0
                    if dept in {"Sales", "Marketing"} and m in {10, 11, 12}:
                        season_bump = 1.05
                    value = dept_monthly_budget * season_bump * np.random.uniform(0.95, 1.05)
                    months[m] = value

                total = sum(months.values())
                row = {
                    "company": company["id"],
                    "department": dept,
                    "category": category,
                    "jan": months[1],
                    "feb": months[2],
                    "mar": months[3],
                    "apr": months[4],
                    "may": months[5],
                    "jun": months[6],
                    "jul": months[7],
                    "aug": months[8],
                    "sep": months[9],
                    "oct": months[10],
                    "nov": months[11],
                    "dec": months[12],
                    "total": total,
                }
                rows.append(row)

    return pd.DataFrame(rows)


def generate_kpi_history(companies: list[dict], periods: int = 36) -> pd.DataFrame:
    """
    Generate KPI history per spec:
        company, period, kpi_name, value, target
    """
    rows: list[dict] = []
    dates = pd.date_range("2023-01-01", periods=periods, freq="MS")

    for company in companies:
        industry = company["industry"]
        base_arr = company["revenue"] if industry in {"SaaS", "FinTech", "Healthcare IT"} else 0.0
        customers = 800 if industry == "SaaS" else 400

        for i, period in enumerate(dates):
            period_str = period.strftime("%Y-%m")
            growth_factor = (1 + company["growth"]) ** (i / 12.0)

            if industry in {"SaaS", "FinTech", "Healthcare IT"}:
                arr = base_arr * growth_factor * np.random.uniform(0.95, 1.05)
                mrr = arr / 12.0
                customers_t = customers * (1 + 0.02 * i / 12.0) * np.random.uniform(0.97, 1.05)
                churn = np.random.uniform(0.02, 0.05)
                net_retention = np.random.uniform(1.1, 1.25)
                cac = np.random.uniform(10_000, 18_000)
                ltv = np.random.uniform(150_000, 220_000)
                cac_payback = np.random.uniform(6.0, 12.0)

                kpis = {
                    "arr": arr,
                    "mrr": mrr,
                    "customers": customers_t,
                    "churn_rate": churn,
                    "net_retention": net_retention,
                    "cac": cac,
                    "ltv": ltv,
                    "cac_payback_months": cac_payback,
                }
            else:
                revenue = company["revenue"] * growth_factor * np.random.uniform(0.95, 1.05)
                gross_margin = np.random.uniform(0.28, 0.42)
                ebitda_margin = np.random.uniform(0.10, 0.24)
                inventory_turns = np.random.uniform(3.0, 6.0) if industry in {"Manufacturing", "Logistics"} else np.nan
                on_time_delivery = np.random.uniform(0.90, 0.98) if industry == "Logistics" else np.nan

                kpis = {
                    "revenue": revenue,
                    "gross_margin": gross_margin,
                    "ebitda_margin": ebitda_margin,
                    "inventory_turns": inventory_turns,
                    "on_time_delivery": on_time_delivery,
                }

            for name, value in kpis.items():
                if pd.isna(value):
                    continue
                # Targets are slightly better than current value
                target = value * np.random.uniform(1.02, 1.08) if name not in {
                    "churn_rate",
                    "cac",
                    "cac_payback_months",
                } else value * np.random.uniform(0.92, 0.98)

                rows.append(
                    {
                        "company": company["id"],
                        "period": period_str,
                        "kpi_name": name,
                        "value": float(value),
                        "target": float(target),
                    }
                )

    return pd.DataFrame(rows)


def generate_driver_data(companies: list[dict], periods: int = 36) -> pd.DataFrame:
    """
    Generate driver data per spec:
        company, period, driver_name, value
    """
    rows: list[dict] = []
    dates = pd.date_range("2023-01-01", periods=periods, freq="MS")

    for company in companies:
        industry = company["industry"]
        base_employees = max(int(company["revenue"] / 250_000), 50)

        for i, period in enumerate(dates):
            period_str = period.strftime("%Y-%m")
            employees_total = base_employees * (1 + company["growth"] * i / 36.0) * np.random.uniform(0.96, 1.06)
            employees_total = int(employees_total)

            # Split by function where relevant
            if industry in {"SaaS", "FinTech", "Healthcare IT"}:
                employees_sales = int(employees_total * np.random.uniform(0.20, 0.30))
                employees_engineering = int(employees_total * np.random.uniform(0.30, 0.40))
                employees_cs = int(employees_total * np.random.uniform(0.10, 0.18))
                avg_contract_value = np.random.uniform(30_000, 60_000)
                sales_cycle_days = np.random.uniform(55, 80)

                drivers = {
                    "employees_total": employees_total,
                    "employees_sales": employees_sales,
                    "employees_engineering": employees_engineering,
                    "employees_customer_success": employees_cs,
                    "average_contract_value": avg_contract_value,
                    "sales_cycle_days": sales_cycle_days,
                }
            elif industry == "Logistics":
                square_footage = np.random.uniform(300_000, 800_000)
                packages_delivered = np.random.uniform(1_500_000, 3_500_000)
                vehicles = np.random.uniform(60, 120)

                drivers = {
                    "employees_total": employees_total,
                    "square_footage": square_footage,
                    "packages_delivered": packages_delivered,
                    "vehicles": vehicles,
                }
            elif industry == "Manufacturing":
                plants = np.random.randint(2, 6)
                capacity_utilization = np.random.uniform(0.7, 0.9)

                drivers = {
                    "employees_total": employees_total,
                    "plants": plants,
                    "capacity_utilization": capacity_utilization,
                }
            else:
                drivers = {
                    "employees_total": employees_total,
                    "field_teams": int(employees_total * np.random.uniform(0.25, 0.40)),
                }

            for name, value in drivers.items():
                rows.append(
                    {
                        "company": company["id"],
                        "period": period_str,
                        "driver_name": name,
                        "value": float(value),
                    }
                )

    return pd.DataFrame(rows)


def generate_strategic_plans(companies: list[dict]) -> list[dict]:
    """
    Generate strategic plan JSON structures per company.
    Structure is compatible with the example in the spec.
    """
    plans: list[dict] = []
    for company in companies:
        base_rev = company["revenue"]
        growth = company["growth"]
        industry = company["industry"]

        # 3-year horizon: 2026-2028
        strategic_targets = {}
        current_year = 2026
        projected_rev = base_rev * (1 + growth) ** 2
        for year in range(current_year, current_year + 3):
            projected_rev *= 1 + growth * 0.8
            if industry == "SaaS":
                ebitda_margin = 0.15 + 0.02 * (year - current_year)
                arr = projected_rev
                nrr = 1.15 + 0.02 * (year - current_year)
            elif industry in {"FinTech", "Healthcare IT"}:
                ebitda_margin = 0.18 + 0.015 * (year - current_year)
                arr = projected_rev * 0.7
                nrr = 1.12 + 0.015 * (year - current_year)
            else:
                ebitda_margin = 0.14 + 0.01 * (year - current_year)
                arr = None
                nrr = None

            year_target = {
                "revenue": round(projected_rev, 2),
                "ebitda_margin": round(ebitda_margin, 4),
            }
            if arr is not None:
                year_target["arr"] = round(arr, 2)
            if nrr is not None:
                year_target["net_revenue_retention"] = round(nrr, 4)

            strategic_targets[str(year)] = year_target

        plan = {
            "company": company["id"],
            "plan_horizon": "2026-2028",
            "strategic_targets": strategic_targets,
            "key_initiatives": [
                {
                    "name": "Enterprise Tier Launch",
                    "timeline": "Q2 2026",
                    "revenue_impact": round(base_rev * 0.2, 2),
                    "investment_required": round(base_rev * 0.05, 2),
                },
                {
                    "name": "International Expansion",
                    "timeline": "Q1 2027",
                    "revenue_impact": round(base_rev * 0.25, 2),
                    "investment_required": round(base_rev * 0.08, 2),
                },
            ],
        }
        plans.append(plan)

    return plans


def generate_initiatives(companies: list[dict]) -> pd.DataFrame:
    """
    Generate strategic initiatives table per spec:
        initiative_id,company,name,category,start_date,investment,annual_revenue_impact,irr,status
    """
    rows: list[dict] = []
    categories = ["Product", "CapEx", "M&A", "Go-To-Market"]
    statuses = ["Planning", "Evaluation", "In Progress", "Completed"]
    counter = 1

    for company in companies:
        for _ in range(3):
            category = np.random.choice(categories)
            status = np.random.choice(statuses, p=[0.3, 0.3, 0.3, 0.1])
            investment = company["revenue"] * np.random.uniform(0.02, 0.08)
            revenue_impact = investment * np.random.uniform(1.5, 4.0)
            irr = np.random.uniform(0.18, 0.5)

            row = {
                "initiative_id": f"INIT-{counter:03d}",
                "company": company["id"],
                "name": f"{category} Initiative {counter}",
                "category": category,
                "start_date": f"2026-{np.random.randint(1, 13):02d}-01",
                "investment": investment,
                "annual_revenue_impact": revenue_impact,
                "irr": irr,
                "status": status,
            }
            rows.append(row)
            counter += 1

    return pd.DataFrame(rows)


def generate_market_benchmarks() -> pd.DataFrame:
    """
    Generate market benchmarks table per spec:
        industry,metric,p25,median,p75,p90
    """
    rows = [
        # SaaS
        {"industry": "SaaS", "metric": "revenue_growth", "p25": 0.25, "median": 0.35, "p75": 0.50, "p90": 0.70},
        {"industry": "SaaS", "metric": "gross_margin", "p25": 0.70, "median": 0.75, "p75": 0.80, "p90": 0.85},
        {
            "industry": "SaaS",
            "metric": "sales_marketing_pct_revenue",
            "p25": 0.40,
            "median": 0.45,
            "p75": 0.50,
            "p90": 0.55,
        },
        {"industry": "SaaS", "metric": "net_retention", "p25": 1.10, "median": 1.15, "p75": 1.20, "p90": 1.25},
        # Manufacturing
        {"industry": "Manufacturing", "metric": "revenue_growth", "p25": 0.05, "median": 0.08, "p75": 0.12, "p90": 0.18},
        {"industry": "Manufacturing", "metric": "gross_margin", "p25": 0.30, "median": 0.35, "p75": 0.40, "p90": 0.45},
        # Logistics
        {"industry": "Logistics", "metric": "revenue_growth", "p25": 0.08, "median": 0.12, "p75": 0.18, "p90": 0.25},
        {"industry": "Logistics", "metric": "ebitda_margin", "p25": 0.08, "median": 0.12, "p75": 0.16, "p90": 0.22},
        # Services
        {"industry": "Services", "metric": "revenue_growth", "p25": 0.04, "median": 0.07, "p75": 0.10, "p90": 0.15},
        {"industry": "Services", "metric": "ebitda_margin", "p25": 0.10, "median": 0.15, "p75": 0.20, "p90": 0.25},
        # FinTech / Healthcare IT
        {"industry": "FinTech", "metric": "revenue_growth", "p25": 0.35, "median": 0.55, "p75": 0.75, "p90": 0.95},
        {"industry": "Healthcare IT", "metric": "revenue_growth", "p25": 0.18, "median": 0.25, "p75": 0.35, "p90": 0.45},
    ]
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="./assignment2_data", help="Output directory for generated data")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    hist_dir = output_dir / "historical_financials"
    budgets_dir = output_dir / "department_budgets"
    kpi_dir = output_dir / "kpi_history"
    driver_dir = output_dir / "driver_data"
    initiatives_dir = output_dir / "initiatives"
    strategic_dir = output_dir / "strategic_plans"
    benchmarks_dir = output_dir / "market_benchmarks"

    for d in [
        hist_dir,
        budgets_dir,
        kpi_dir,
        driver_dir,
        initiatives_dir,
        strategic_dir,
        benchmarks_dir,
    ]:
        d.mkdir(parents=True, exist_ok=True)

    print("Generating Assignment 2 FP&A planning data...")

    # Historical financials
    hist = generate_historical_financials(COMPANIES, periods=36)
    hist.to_csv(hist_dir / "historical_financials.csv", index=False)
    print(f"Historical financials: {len(hist)} records "
          f"(~{len(hist) // len(COMPANIES)} per company)")

    # Department budgets
    budgets = generate_department_budgets(COMPANIES)
    budgets.to_csv(budgets_dir / "department_budgets.csv", index=False)
    print(f"Department budgets: {len(budgets)} rows")

    # KPI history
    kpis = generate_kpi_history(COMPANIES, periods=36)
    kpis.to_csv(kpi_dir / "kpi_history.csv", index=False)
    print(f"KPI history: {len(kpis)} records")

    # Driver data
    drivers = generate_driver_data(COMPANIES, periods=36)
    drivers.to_csv(driver_dir / "driver_data.csv", index=False)
    print(f"Driver data: {len(drivers)} records")

    # Strategic initiatives
    initiatives = generate_initiatives(COMPANIES)
    initiatives.to_csv(initiatives_dir / "initiatives.csv", index=False)
    print(f"Strategic initiatives: {len(initiatives)} rows")

    # Strategic plans (JSON per company)
    plans = generate_strategic_plans(COMPANIES)
    for plan in plans:
        with open(strategic_dir / f"{plan['company']}_plan.json", "w") as f:
            json.dump(plan, f, indent=2)
    print(f"Strategic plans: {len(plans)} JSON files")

    # Market benchmarks
    benchmarks = generate_market_benchmarks()
    benchmarks.to_csv(benchmarks_dir / "market_benchmarks.csv", index=False)
    print(f"Market benchmarks: {len(benchmarks)} rows")

    # README
    readme_path = output_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write(
            f"# Assignment 2 Sample Data\n"
            f"Generated: {datetime.now()}\n\n"
            f"## Folders and Files\n"
            f"- historical_financials/historical_financials.csv: 36 months P&L + BS + CF metrics (tall format)\n"
            f"- department_budgets/department_budgets.csv: Departmental budgets in wide format\n"
            f"- kpi_history/kpi_history.csv: 36 months of KPI history per company\n"
            f"- driver_data/driver_data.csv: 36 months of driver metrics per company\n"
            f"- initiatives/initiatives.csv: Strategic initiatives per company\n"
            f"- strategic_plans/*.json: Strategic plans per company\n"
            f"- market_benchmarks/market_benchmarks.csv: Industry benchmark metrics\n\n"
            f"## Notes\n"
            f"- Historical financials include revenue, costs, EBITDA, simple balance sheet, and cash flow metrics.\n"
            f"- Data includes growth trends, industry-specific seasonality, and realistic margin patterns.\n"
        )

    total_records = (
        len(hist)
        + len(budgets)
        + len(kpis)
        + len(drivers)
        + len(initiatives)
        + len(benchmarks)
    )
    print(f"Total tabular records (excluding JSON plans): {total_records}")
    print(f"Data written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()

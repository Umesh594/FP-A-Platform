# backend/scripts/seed_data.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
from datetime import date
from app.database import SessionLocal, Base, engine
from app.models.company import Company
from app.models.financials import FinancialMetric
from app.models.kpi import KPI
from app.models.initiative import Initiative
from app.models.driver import DriverMetric

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Always reset demo data back to the provided assignment seed files.
for model in (DriverMetric, KPI, Initiative, FinancialMetric, Company):
    db.query(model).delete()
db.commit()
print("Existing seeded tables cleared")

# --- 1. Insert Companies ---
companies_data = [
    dict(id=1, name="CloudCRM Inc",              sector="SaaS",          revenue=35_200_000,  ebitda=7_800_000,  arr=35_000_000, employees=280),
    dict(id=2, name="ManufactureTech Co",         sector="Manufacturing", revenue=95_400_000,  ebitda=14_300_000, arr=0,          employees=820),
    dict(id=3, name="HealthcareTech Solutions",   sector="Healthcare IT", revenue=55_100_000,  ebitda=9_900_000,  arr=22_000_000, employees=410),
    dict(id=4, name="E-commerce Logistics",       sector="Logistics",     revenue=140_600_000, ebitda=16_900_000, arr=0,          employees=1450),
    dict(id=5, name="FinTech Payments",           sector="FinTech",       revenue=28_300_000,  ebitda=3_400_000,  arr=28_000_000, employees=150),
    dict(id=6, name="Industrial Services Group",  sector="Industrial",    revenue=180_200_000, ebitda=27_000_000, arr=0,          employees=2200),
]
for c in companies_data:
    db.add(Company(**c))
db.commit()
print("Companies seeded")

# --- 2. Load Historical Financials ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "assignment2_data", "historical_financials")
hist_path = os.path.join(DATA_DIR, "historical_financials.csv")

company_id_map = {
    "cloudcrm_inc": 1, "manufacturetech_co": 2, "healthcaretech": 3,
    "ecommerce_logistics": 4, "fintech_payments": 5, "industrial_services": 6,
}

if os.path.exists(hist_path):
    df = pd.read_csv(hist_path)
    pivoted = df.pivot_table(index=["company", "period"], columns="metric", values="value", aggfunc="first").reset_index()
    count = 0
    for _, row in pivoted.iterrows():
        cid = company_id_map.get(row["company"])
        if not cid:
            continue
        period = date.fromisoformat(row["period"] + "-01") if len(str(row["period"])) == 7 else date.fromisoformat(str(row["period"]))
        db.add(FinancialMetric(
            company_id=cid, period=period,
            revenue=float(row.get("revenue", 0) or 0),
            cogs=float(row.get("cogs", 0) or 0),
            gross_profit=float(row.get("gross_profit", 0) or 0),
            ebitda=float(row.get("ebitda", 0) or 0),
            customer_count=None, price_per_customer=None,
        ))
        count += 1
    db.commit()
    print(f"Financial metrics seeded: {count} rows")
else:
    print(f"Historical financials CSV not found at: {hist_path}")
    print("Run: python generate_assignment2_data.py --output ../../assignment2_data first")

# --- 3. Seed KPIs ---
kpi_path = os.path.join(os.path.dirname(__file__), "..", "assignment2_data", "kpi_history", "kpi_history.csv")
if os.path.exists(kpi_path):
    df = pd.read_csv(kpi_path)
    count = 0
    for _, row in df.iterrows():
        cid = company_id_map.get(row["company"])
        if not cid:
            continue
        period = date.fromisoformat(row["period"] + "-01") if len(str(row["period"])) == 7 else date.fromisoformat(str(row["period"]))
        name = str(row.get("kpi_name") or "").strip()
        if not name:
            continue
        db.add(KPI(
            company_id=cid,
            name=name,
            actual=float(row.get("value", 0) or 0),
            target=float(row.get("target", 0) or 0),
            status="",
            period=period
        ))
        count += 1
    db.commit()
    print(f"KPIs seeded: {count} rows")
else:
    print(f"KPI history CSV not found at: {kpi_path}")

# --- 4. Seed Initiatives ---
initiative_path = os.path.join(os.path.dirname(__file__), "..", "assignment2_data", "initiatives", "initiatives.csv")
if os.path.exists(initiative_path):
    df = pd.read_csv(initiative_path)
    count = 0
    for _, row in df.iterrows():
        cid = company_id_map.get(row["company"])
        if not cid:
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        start_date = row.get("start_date")
        start = date.fromisoformat(start_date) if isinstance(start_date, str) else None
        db.add(Initiative(
            company_id=cid,
            name=name,
            description=str(row.get("category") or ""),
            investment=float(row.get("investment", 0) or 0),
            revenue_impact=float(row.get("annual_revenue_impact", 0) or 0),
            start_date=start
        ))
        count += 1
    db.commit()
    print(f"Initiatives seeded: {count} rows")
else:
    print(f"Initiatives CSV not found at: {initiative_path}")

# --- 5. Seed Driver Data ---
driver_path = os.path.join(os.path.dirname(__file__), "..", "assignment2_data", "driver_data", "driver_data.csv")
if os.path.exists(driver_path):
    df = pd.read_csv(driver_path)
    count = 0
    for _, row in df.iterrows():
        cid = company_id_map.get(row["company"])
        if not cid:
            continue
        period = date.fromisoformat(row["period"] + "-01") if len(str(row["period"])) == 7 else date.fromisoformat(str(row["period"]))
        driver_name = str(row.get("driver_name") or "").strip()
        if not driver_name:
            continue
        db.add(DriverMetric(company_id=cid, period=period, driver_name=driver_name, value=float(row.get("value", 0) or 0)))
        count += 1
    db.commit()
    print(f"Driver metrics seeded: {count} rows")
else:
    print(f"Driver CSV not found at: {driver_path}")

db.close()
print("All data seeded successfully. Database ready.")

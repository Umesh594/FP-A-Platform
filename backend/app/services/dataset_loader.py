import re
from dataclasses import dataclass
from typing import Dict, Iterable

import pandas as pd
from sqlalchemy.orm import Session

from app.models.financials import FinancialMetric
from app.models.company import Company
from app.models.driver import DriverMetric
from app.logger import logger


@dataclass
class LoadResult:
    rows_loaded: int
    company_ids: Dict[str, int]


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower()) if value else ""


def _build_company_lookup(db: Session) -> Dict[str, int]:
    companies = db.query(Company).all()
    lookup: Dict[str, int] = {}
    for c in companies:
        lookup[str(c.id)] = c.id
        lookup[_normalize_key(c.name)] = c.id
        lookup[_normalize_key(c.name.replace(" ", "_"))] = c.id
        tokens = re.split(r"\s+", c.name.strip())
        if tokens:
            lookup[_normalize_key(tokens[0])] = c.id
        if len(tokens) > 1:
            lookup[_normalize_key("".join(tokens[:2]))] = c.id
    return lookup


def _resolve_company_id(raw: str, lookup: Dict[str, int]) -> int | None:
    if raw is None:
        return None
    key = str(raw).strip()
    if key in lookup:
        return lookup[key]
    norm = _normalize_key(key)
    if norm in lookup:
        return lookup[norm]
    # fallback: prefix match (e.g., healthcaretech -> healthcaretechsolutions)
    for k, v in lookup.items():
        if k.startswith(norm):
            return v
    return None


def _to_period_date(value: str) -> pd.Timestamp:
    # Accept YYYY-MM or full ISO date
    val = str(value)
    if len(val) == 7:
        val = f"{val}-01"
    return pd.to_datetime(val, errors="coerce")


def load_financial_csv(file_path: str, db: Session) -> LoadResult:
    """
    Load financial CSV data into FinancialMetric.

    Supported formats:
    1) Tall: company, period, metric, value
    2) Wide: company or company_id + revenue/cogs/gross_profit/ebitda columns
    """
    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError("Uploaded CSV is empty")

    lookup = _build_company_lookup(db)

    # Detect tall format
    if {"company", "period", "metric", "value"}.issubset(df.columns):
        pivoted = (
            df.pivot_table(
                index=["company", "period"],
                columns="metric",
                values="value",
                aggfunc="first",
            )
            .reset_index()
        )
    # Detect wide format
    elif {"period", "revenue", "cogs", "gross_profit", "ebitda"}.issubset(df.columns):
        pivoted = df.copy()
        if "company" not in pivoted.columns and "company_id" not in pivoted.columns:
            raise ValueError("Wide CSV must include 'company' or 'company_id'")
    else:
        raise ValueError("Unsupported CSV format. Expected tall (company, period, metric, value) or wide with revenue/cogs/gross_profit/ebitda.")

    rows_loaded = 0
    company_ids: Dict[str, int] = {}

    for _, row in pivoted.iterrows():
        raw_company = row.get("company_id", row.get("company"))
        company_id = _resolve_company_id(raw_company, lookup)
        if not company_id:
            logger.warning("Skipping row with unknown company: %s", raw_company)
            continue

        period_ts = _to_period_date(row.get("period"))
        if pd.isna(period_ts):
            logger.warning("Skipping row with invalid period: %s", row.get("period"))
            continue

        revenue = float(row.get("revenue", 0) or 0)
        cogs = float(row.get("cogs", 0) or 0)
        gross_profit = row.get("gross_profit")
        if gross_profit is None:
            gross_profit = revenue - cogs
        else:
            gross_profit = float(gross_profit or 0)

        ebitda = row.get("ebitda")
        if ebitda is None:
            sales_marketing = float(row.get("sales_marketing", 0) or 0)
            rd = float(row.get("rd", 0) or 0)
            ga = float(row.get("ga", 0) or 0)
            ebitda = gross_profit - (sales_marketing + rd + ga)
        else:
            ebitda = float(ebitda or 0)

        period = period_ts.date()
        existing = (
            db.query(FinancialMetric)
            .filter_by(company_id=company_id, period=period)
            .first()
        )

        if existing:
            existing.revenue = revenue
            existing.cogs = cogs
            existing.gross_profit = gross_profit
            existing.ebitda = ebitda
        else:
            db.add(
                FinancialMetric(
                    company_id=company_id,
                    period=period,
                    revenue=revenue,
                    cogs=cogs,
                    gross_profit=gross_profit,
                    ebitda=ebitda,
                    customer_count=None,
                    price_per_customer=None,
                )
            )

        rows_loaded += 1
        company_ids[str(raw_company)] = company_id

    db.commit()
    logger.info("Loaded %s financial rows from %s", rows_loaded, file_path)
    return LoadResult(rows_loaded=rows_loaded, company_ids=company_ids)


def load_driver_csv(file_path: str, db: Session) -> LoadResult:
    """
    Load driver CSV data: company, period, driver_name, value.
    """
    df = pd.read_csv(file_path)

    required_columns = {"company", "period", "driver_name", "value"}
    if not required_columns.issubset(df.columns):
        if {"company", "period", "metric", "value"}.issubset(df.columns):
            raise ValueError("This looks like historical_financials.csv. Use /financials/upload-financials instead.")
        raise ValueError("Driver CSV must contain company, period, driver_name, value")

    lookup = _build_company_lookup(db)
    rows_loaded = 0
    company_ids: Dict[str, int] = {}

    for _, row in df.iterrows():
        raw_company = row.get("company")
        company_id = _resolve_company_id(raw_company, lookup)
        if not company_id:
            logger.warning("Skipping driver row with unknown company: %s", raw_company)
            continue

        period_ts = _to_period_date(row.get("period"))
        if pd.isna(period_ts):
            logger.warning("Skipping driver row with invalid period: %s", row.get("period"))
            continue

        driver_name = str(row.get("driver_name") or "").strip()
        if not driver_name:
            logger.warning("Skipping driver row with empty driver_name")
            continue

        value = float(row.get("value", 0) or 0)
        period = period_ts.date()

        existing = (
            db.query(DriverMetric)
            .filter_by(company_id=company_id, period=period, driver_name=driver_name)
            .first()
        )

        if existing:
            existing.value = value
        else:
            db.add(
                DriverMetric(
                    company_id=company_id,
                    period=period,
                    driver_name=driver_name,
                    value=value,
                )
            )

        rows_loaded += 1
        company_ids[str(raw_company)] = company_id

    db.commit()
    logger.info("Loaded %s driver rows from %s", rows_loaded, file_path)
    return LoadResult(rows_loaded=rows_loaded, company_ids=company_ids)


def resolve_company_ids_from_csv(file_path: str, db: Session) -> Dict[str, int]:
    df = pd.read_csv(file_path)
    lookup = _build_company_lookup(db)
    ids: Dict[str, int] = {}

    if "company_id" in df.columns:
        for raw in df["company_id"].dropna().unique().tolist():
            cid = _resolve_company_id(raw, lookup)
            if cid:
                ids[str(raw)] = cid
    elif "company" in df.columns:
        for raw in df["company"].dropna().unique().tolist():
            cid = _resolve_company_id(raw, lookup)
            if cid:
                ids[str(raw)] = cid

    return ids

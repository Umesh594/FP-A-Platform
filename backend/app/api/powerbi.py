from fastapi import APIRouter, Depends
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.company import Company
from app.models.financials import FinancialMetric
from app.models.initiative import Initiative
from app.models.kpi import KPI

router = APIRouter(prefix="/powerbi", tags=["powerbi"])


@router.get("/executive-dataset")
def executive_dataset(db: Session = Depends(get_db)):
    """BI-ready fact rows at company-period grain for Power BI refresh."""
    financial_rows = (
        db.query(FinancialMetric, Company)
        .join(Company, FinancialMetric.company_id == Company.id)
        .order_by(FinancialMetric.period, Company.name)
        .all()
    )

    kpi_subquery = (
        db.query(
            KPI.company_id.label("company_id"),
            KPI.period.label("period"),
            func.count(KPI.id).label("kpi_count"),
            func.sum(case((KPI.status == "At Risk", 1), else_=0)).label("at_risk_kpis"),
            func.avg(KPI.actual / func.nullif(KPI.target, 0)).label("kpi_attainment"),
        )
        .group_by(KPI.company_id, KPI.period)
        .subquery()
    )

    kpis_by_key = {
        (row.company_id, row.period): row
        for row in db.query(kpi_subquery).all()
    }

    rows = []
    for metric, company in financial_rows:
        kpi = kpis_by_key.get((metric.company_id, metric.period))
        gross_margin = (metric.gross_profit / metric.revenue) if metric.revenue else 0
        ebitda_margin = (metric.ebitda / metric.revenue) if metric.revenue else 0
        rows.append(
            {
                "date_key": int(metric.period.strftime("%Y%m%d")),
                "period": metric.period.isoformat(),
                "month": metric.period.strftime("%Y-%m"),
                "company_id": company.id,
                "company_name": company.name,
                "sector": company.sector,
                "revenue": round(metric.revenue or 0, 2),
                "gross_profit": round(metric.gross_profit or 0, 2),
                "ebitda": round(metric.ebitda or 0, 2),
                "gross_margin": round(gross_margin, 4),
                "ebitda_margin": round(ebitda_margin, 4),
                "customer_count": metric.customer_count,
                "price_per_customer": metric.price_per_customer,
                "kpi_count": int(kpi.kpi_count or 0) if kpi else 0,
                "at_risk_kpis": int(kpi.at_risk_kpis or 0) if kpi else 0,
                "kpi_attainment": round(float(kpi.kpi_attainment or 0), 4) if kpi else 0,
            }
        )
    return rows


@router.get("/data-quality-scorecard")
def data_quality_scorecard(db: Session = Depends(get_db)):
    total_financial_rows = db.query(FinancialMetric).count()
    missing_revenue = db.query(FinancialMetric).filter(FinancialMetric.revenue.is_(None)).count()
    missing_ebitda = db.query(FinancialMetric).filter(FinancialMetric.ebitda.is_(None)).count()
    companies = db.query(Company).count()
    initiative_rows = db.query(Initiative).count()
    kpi_rows = db.query(KPI).count()
    completeness = 1 - ((missing_revenue + missing_ebitda) / max(total_financial_rows * 2, 1))

    return {
        "financial_rows": total_financial_rows,
        "companies": companies,
        "kpi_rows": kpi_rows,
        "initiative_rows": initiative_rows,
        "missing_revenue_rows": missing_revenue,
        "missing_ebitda_rows": missing_ebitda,
        "financial_completeness_pct": round(completeness * 100, 2),
        "powerbi_refresh_status": "ready" if completeness >= 0.98 else "review",
    }

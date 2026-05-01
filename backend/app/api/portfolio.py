from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.company import Company
from app.models.financials import FinancialMetric

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

@router.get("/summary")
def portfolio_summary(db: Session = Depends(get_db)):
    companies = db.query(Company).all()

    result = []

    for c in companies:
        rows = db.query(FinancialMetric).filter(
            FinancialMetric.company_id == c.id
        ).order_by(FinancialMetric.period).all()

        latest = rows[-1] if rows else None

        result.append({
            "company": c.name,
            "revenue": latest.revenue if latest else 0,
            "ebitda": latest.ebitda if latest else 0
        })

    return result
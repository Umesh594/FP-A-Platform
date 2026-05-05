from sqlalchemy.orm import Session

from app.models.financials import FinancialMetric


def extract_seeded_financials(db: Session) -> list[dict]:
    rows = db.query(FinancialMetric).order_by(FinancialMetric.company_id, FinancialMetric.period).all()
    return [
        {
            "company_id": row.company_id,
            "period": row.period,
            "revenue": row.revenue,
            "cogs": row.cogs,
            "gross_profit": row.gross_profit,
            "ebitda": row.ebitda,
            "customer_count": row.customer_count,
            "price_per_customer": row.price_per_customer,
        }
        for row in rows
    ]

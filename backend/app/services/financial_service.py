import asyncio
from app.agents.revenue_agent import RevenueForecastAgent
from app.agents.expense_agent import ExpenseForecastAgent
from app.agents.capital_agent import CapitalPlanningAgent
from sqlalchemy.orm import Session
from app.logger import logger
from app.utils.json_sanitize import sanitize_for_json

async def generate_financial_forecast(company_id: int, db: Session):
    """
    Fetch forecasts from all relevant agents.
    Handles empty DB gracefully.
    """
    try:
        revenue_agent = RevenueForecastAgent()
        expense_agent = ExpenseForecastAgent()
        capital_agent = CapitalPlanningAgent()

        revenue, expense, capital = await asyncio.gather(
            revenue_agent.run(company_id, db),
            expense_agent.run(company_id, db),
            capital_agent.run(db)
        )

        result = {
            "revenue_forecast": revenue.get("forecast", []),
            "expense_forecast": expense.get("forecast", []),
            "revenue": revenue.get("forecast", []),
            "expense": expense.get("forecast", []),
            "capital": capital.get("analysis", []),
            "error": None
        }
        return sanitize_for_json(result)
    except Exception as e:
        logger.exception(f"generate_financial_forecast failed: {e}")
        return {
            "error": str(e),
            "revenue_forecast": [],
            "expense_forecast": [],
            "revenue": [],
            "expense": [],
            "capital": [],
        }


def get_financial_history(company_id: int, db: Session):
    """
    Fetch historical financial metrics.
    Handles empty DB gracefully.
    """
    from app.models.financials import FinancialMetric

    try:
        rows = db.query(FinancialMetric).filter(FinancialMetric.company_id == company_id).order_by(FinancialMetric.period).all()
        if not rows:
            return []

        history = []
        for r in rows:
            history.append({
                "period": r.period,
                "revenue": r.revenue,
                "cogs": r.cogs,
                "gross_profit": r.gross_profit,
                "ebitda": r.ebitda,
                "customer_count": r.customer_count,
                "price_per_customer": r.price_per_customer
            })
        return history
    except Exception as e:
        logger.exception(f"get_financial_history failed: {e}")
        return []

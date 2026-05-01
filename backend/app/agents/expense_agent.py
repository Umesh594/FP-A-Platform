from agno.agent import Agent
from sqlalchemy.orm import Session
import pandas as pd
from app.models.financials import FinancialMetric
from app.utils.forecasting import rolling_forecast
from app.logger import logger

class ExpenseForecastAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "Expense Forecasting Agent"

    async def run(self, company_id: int, db: Session):
        try:
            rows = db.query(FinancialMetric).filter(
                FinancialMetric.company_id == company_id
            ).order_by(FinancialMetric.period).all()
            if not rows:
                return {"agent": self.name, "error": "No financial data"}

            cogs_rows = []
            opex_rows = []
            for r in rows:
                revenue = r.revenue or 0
                ebitda = r.ebitda or 0
                cogs = r.cogs or 0
                gross_profit = r.gross_profit if r.gross_profit is not None else (revenue - cogs)
                opex = gross_profit - ebitda

                cogs_rows.append({"ds": r.period, "y": cogs})
                opex_rows.append({"ds": r.period, "y": opex})

            cogs_df = pd.DataFrame(cogs_rows)
            opex_df = pd.DataFrame(opex_rows)
            if cogs_df.empty or opex_df.empty:
                return {"agent": self.name, "error": "No expense data"}

            cogs_forecast = rolling_forecast(cogs_df, months=12)
            opex_forecast = rolling_forecast(opex_df, months=12)

            # Merge by ds and compute total expense
            merged = pd.merge(
                cogs_forecast[["ds", "yhat"]],
                opex_forecast[["ds", "yhat"]],
                on="ds",
                how="inner",
                suffixes=("_cogs", "_opex"),
            )
            merged["yhat"] = merged["yhat_cogs"] + merged["yhat_opex"]
            forecast = merged[["ds", "yhat"]]

            return {"agent": self.name, "forecast": forecast.to_dict(orient="records")}
        except Exception as e:
            logger.exception(f"ExpenseForecastAgent failed: {e}")
            return {"agent": self.name, "error": str(e)}

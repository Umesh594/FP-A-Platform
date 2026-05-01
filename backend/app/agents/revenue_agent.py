from agno.agent import Agent
from sqlalchemy.orm import Session
import pandas as pd
from app.models.financials import FinancialMetric
from app.utils.forecasting import rolling_forecast
from app.logger import logger


class RevenueForecastAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "Revenue Forecast Agent"

    async def run(self, company_id: int, db: Session):
        try:
            rows = db.query(FinancialMetric).filter(
                FinancialMetric.company_id == company_id
            ).order_by(FinancialMetric.period).all()

            if not rows:
                return {"agent": self.name, "error": "No historical financial data"}

            data = []

            for r in rows:
                # 🔥 Driver-based revenue (primary)
                driver_revenue = (r.customer_count or 0) * (r.price_per_customer or 0)

                # 🔥 Fallback to actual revenue
                if driver_revenue <= 0:
                    driver_revenue = r.revenue or 0

                # 🔥 Skip invalid rows
                if driver_revenue <= 0 or not r.period:
                    continue

                data.append({
                    "ds": r.period,
                    "y": driver_revenue
                })

            # 🔥 Safety check after cleaning
            if not data:
                return {"agent": self.name, "error": "No valid data after cleaning"}

            df = pd.DataFrame(data)

            # 🔥 Smooth data (reduce noise)
            df["y"] = df["y"].rolling(3).mean()
            df = df.dropna()

            # 🔥 Ensure enough data
            if len(df) < 2:
                return {"agent": self.name, "error": "Not enough data for forecast"}

            forecast = rolling_forecast(df, months=12)

            return {
                "agent": self.name,
                "company_id": company_id,
                "method": "driver_based_forecast",
                "forecast": forecast.to_dict(orient="records")
            }

        except Exception as e:
            logger.exception(f"RevenueForecastAgent failed: {e}")
            return {"agent": self.name, "error": str(e)}

    async def adjust_forecast(self, forecast, variance):
        try:
            pct = variance.get("percentage", 0) if isinstance(variance, dict) else 0

            # 🔥 Handle % vs ratio
            if abs(pct) > 1:
                pct = pct / 100

            factor = 1 - pct

            adjusted = []

            for f in forecast:
                if isinstance(f, dict) and "yhat" in f:
                    f["yhat"] = f["yhat"] * factor
                adjusted.append(f)

            return adjusted

        except Exception as e:
            logger.exception(f"Adjust forecast failed: {e}")
            return forecast
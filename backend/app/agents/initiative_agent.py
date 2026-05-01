from agno.agent import Agent
from sqlalchemy.orm import Session
from app.models.initiative import Initiative
import numpy_financial as npf
from app.logger import logger

class StrategicInitiativeAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "Strategic Initiative Agent"

    def npv(self, rate, cashflows):
        return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cashflows))

    def irr(self, cashflows):
        try:
            return npf.irr(cashflows)
        except Exception:
            return None

    async def run(self, db: Session, weeks_elapsed: int = 0):
        try:
            initiatives = db.query(Initiative).all()
            results = []

            for i in initiatives:
                investment = i.investment or 0
                impact = i.revenue_impact or 0
                roi = impact / investment if investment else 0

                periods = 4
                progress = min(weeks_elapsed / (periods * 4), 1)

                adjusted_cashflows = [
                    -investment * (1 - progress),
                    impact * progress,
                    impact * (1 - progress),
                    impact * (1 - progress)
                ]

                results.append({
                    "initiative": i.name,
                    "roi": roi,
                    "npv": self.npv(0.1, adjusted_cashflows),
                    "irr": self.irr(adjusted_cashflows),
                    "progress": progress
                })

            return {
                "agent": self.name,
                "initiatives": results
            }

        except Exception as e:
            logger.exception(f"StrategicInitiativeAgent failed: {e}")
            return {"agent": self.name, "error": str(e)}
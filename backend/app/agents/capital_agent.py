from agno.agent import Agent
from sqlalchemy.orm import Session
from app.models.initiative import Initiative
from app.logger import logger
import numpy_financial as npf

class CapitalPlanningAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "Capital Planning Agent"

    def npv(self, rate, cashflows):
        return sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cashflows))

    def irr(self, cashflows):
        try:
            return npf.irr(cashflows)
        except Exception:
            return None

    async def run(self, db: Session, rate: float = 0.1):
        try:
            initiatives = db.query(Initiative).all()
            results = []
            for i in initiatives:
                investment = i.investment or 0
                impact = i.revenue_impact or 0
                # Simple ramp-up with risk weighting
                ramp = [0.0, 0.3, 0.6, 0.9, 1.0]
                risk = 0.85 if investment > 0 else 1.0
                cashflows = [-investment] + [impact * r * risk for r in ramp[1:]]
                results.append({
                    "initiative": i.name,
                    "investment": investment,
                    "expected_return": impact,
                    "cashflow_projection": cashflows,
                    "npv": self.npv(rate, cashflows),
                    "irr": self.irr(cashflows),
                })
            return {"agent": self.name, "analysis": results}
        except Exception as e:
            logger.exception(f"CapitalPlanningAgent failed: {e}")
            return {"agent": self.name, "error": str(e)}

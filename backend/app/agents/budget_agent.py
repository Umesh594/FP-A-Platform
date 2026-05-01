from agno.agent import Agent
from app.logger import logger

class BudgetBuilderAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "Budget Builder Agent"

    async def run(self, revenue_forecast, expense_forecast):
        if not revenue_forecast or not expense_forecast:
            return {"agent": self.name, "budget": []}
        try:
            budget = []
            min_len = min(len(revenue_forecast), len(expense_forecast))
            for i in range(min_len):
                r = revenue_forecast[i]
                e = expense_forecast[i]
                r_val = r.get("yhat", 0)
                e_val = e.get("yhat", 0)
                profit = r_val - e_val
                profit_margin = profit / r_val if r_val else 0
                flags = []
                if profit_margin < 0:
                    flags.append("Loss-making")
                if i > 0:
                    prev = revenue_forecast[i-1].get("yhat", 0)
                    if prev and (r_val / prev) > 1.25:
                        flags.append("Aggressive growth assumption")
                budget.append({
                    "month": r.get("ds"),
                    "revenue": r_val,
                    "expense": e_val,
                    "profit": profit,
                    "profit_margin": profit_margin,
                    "flags": flags
                })
            return {"agent": self.name, "budget": budget}
        except Exception as e:
            logger.exception(f"BudgetBuilderAgent failed: {e}")
            return {"agent": self.name, "error": str(e)}

from agno.agent import Agent
from app.utils.monte_carlo import monte_carlo_simulation
from app.logger import logger
from app.websocket.manager import broadcast
class ScenarioModelingAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "Scenario Modeling Agent"

    async def run(self, base_revenue: float, base_expense: float = None):
        try:
            drivers = {"revenue": base_revenue, "expense": base_expense or base_revenue * 0.8}
            scenarios = {
                "optimistic": monte_carlo_simulation(drivers, volatility=0.05),
                "base": monte_carlo_simulation(drivers, volatility=0.10),
                "pessimistic": monte_carlo_simulation(drivers, volatility=0.20)
            }
            result = {"agent": self.name, "scenarios": scenarios}
            try:
                await broadcast(result)
            except Exception as e:
                logger.warning(f"Scenario WebSocket failed: {e}")
            return result
        except Exception as e:
            logger.exception(f"ScenarioModelingAgent failed: {e}")
            return {"agent": self.name, "error": str(e)}
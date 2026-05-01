from agno.agent import Agent
from sqlalchemy.orm import Session
from app.logger import logger
from app.websocket.manager import broadcast
from app.services.kpi_service import get_kpis

class KPITrackingAgent(Agent):
    def __init__(self):
        super().__init__()
        self.name = "KPI Tracking Agent"

    async def run(self, company_id: int, db: Session):
        try:
            if not company_id:
                return {"agent": self.name, "error": "company_id required"}

            alerts = get_kpis(company_id, db)
            result = {"agent": self.name, "kpis": alerts}

            try:
                await broadcast(result)
            except Exception as e:
                logger.warning(f"KPI WebSocket failed: {e}")

            return result

        except Exception as e:
            logger.exception(f"KPITrackingAgent failed: {e}")
            return {"agent": self.name, "error": str(e)}
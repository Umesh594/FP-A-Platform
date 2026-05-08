from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.utils.json_sanitize import sanitize_for_json

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

@router.post("/run/{company_id}")
async def run_orchestrator(company_id: int, notify_email: str | None = None, db: Session = Depends(get_db)):
    from app.agents.orchestrator_agent import StrategicOrchestrator

    orchestrator = StrategicOrchestrator()
    result = await orchestrator.run_planning_cycle(company_id=company_id, db=db, notify_email=notify_email)
    return sanitize_for_json(result)

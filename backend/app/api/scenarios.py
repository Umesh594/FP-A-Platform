from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.financials import FinancialMetric
from app.utils.json_sanitize import sanitize_for_json

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("/")
async def generate_scenarios_from_assumptions(base_revenue: float, base_expense: float | None = None):
    from app.agents.scenario_agent import ScenarioModelingAgent

    agent = ScenarioModelingAgent()
    result = await agent.run(
        base_revenue=base_revenue,
        base_expense=base_expense if base_expense is not None else base_revenue * 0.8,
    )
    return sanitize_for_json(result)

@router.post("/generate/{company_id}")
async def generate_scenarios(company_id: int, db: Session = Depends(get_db)):
    from app.agents.scenario_agent import ScenarioModelingAgent

    rows = db.query(FinancialMetric).filter(
        FinancialMetric.company_id == company_id
    ).order_by(FinancialMetric.period).all()

    if not rows:
        return {"error": "No data"}

    last = rows[-1]

    agent = ScenarioModelingAgent()
    result = await agent.run(
        base_revenue=last.revenue or 0,
        base_expense=(last.revenue - last.ebitda) if last.ebitda else 0
    )
    return sanitize_for_json(result)


@router.get("/{company_id}")
async def get_scenarios(company_id: int, db: Session = Depends(get_db)):
    from app.agents.scenario_agent import ScenarioModelingAgent

    rows = db.query(FinancialMetric).filter(
        FinancialMetric.company_id == company_id
    ).order_by(FinancialMetric.period).all()

    if not rows:
        return {"error": "No data"}

    last = rows[-1]
    agent = ScenarioModelingAgent()
    result = await agent.run(
        base_revenue=last.revenue or 0,
        base_expense=(last.revenue - last.ebitda) if last.ebitda else 0
    )
    return sanitize_for_json(result)

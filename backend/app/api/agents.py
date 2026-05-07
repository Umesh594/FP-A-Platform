from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.agentic_system import AGENT_GRAPH, get_agent_run, list_agent_runs, run_agentic_cycle
from app.services.enterprise_system import (
    execute_secure_tool,
    list_data_sources,
    list_recommendations,
    observability_summary,
    run_pipeline,
    sync_connector,
    test_connector,
)
from app.evals import run_agent_evals
from app.mcp_server.server import describe_mcp_server
from app.pipelines import run_apache_beam_pipeline, run_spark_pipeline

router = APIRouter(prefix="/agents", tags=["agentic-system"])


class RunCycleRequest(BaseModel):
    company_id: int = 1
    request_type: str = "planning_cycle"


class SecureToolRequest(BaseModel):
    tool_name: str
    tool_input: dict = {}
    role: str = "Admin"


@router.get("/graph")
def graph_definition():
    return {
        "framework": "LangGraph-style deterministic orchestration",
        "patterns": ["ReAct", "self-reflection", "hierarchical delegation", "tool-calling"],
        "agents": AGENT_GRAPH,
        "edges": [
            ["Orchestrator Agent", "Revenue Forecasting Agent"],
            ["Orchestrator Agent", "Expense Forecasting Agent"],
            ["Orchestrator Agent", "KPI Monitoring Agent"],
            ["Orchestrator Agent", "Variance Analysis Agent"],
            ["Orchestrator Agent", "Scenario Modeling Agent"],
            ["Orchestrator Agent", "Budget Validation Agent"],
            ["Orchestrator Agent", "Capital Planning Agent"],
            ["Orchestrator Agent", "Risk Detection Agent"],
            ["Orchestrator Agent", "Reporting Agent"],
            ["Reporting Agent", "Reflection Agent"],
            ["Reflection Agent", "Evaluation Agent"],
        ],
    }


@router.post("/run-cycle")
async def run_cycle(payload: RunCycleRequest, db: Session = Depends(get_db)):
    return await run_agentic_cycle(db, payload.company_id, payload.request_type)


@router.get("/runs")
def runs(limit: int = 20, db: Session = Depends(get_db)):
    return list_agent_runs(db, limit=limit)


@router.get("/runs/{run_id}")
def run_detail(run_id: str, db: Session = Depends(get_db)):
    result = get_agent_run(db, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return result


@router.get("/observability/summary")
def observability(db: Session = Depends(get_db)):
    return observability_summary(db)


@router.get("/mcp")
def mcp_server():
    return describe_mcp_server()


@router.post("/evals/{run_id}")
def run_evals(run_id: str, db: Session = Depends(get_db)):
    result = run_agent_evals(db, run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return result


@router.get("/recommendations")
def recommendations(company_id: int | None = None, db: Session = Depends(get_db)):
    return list_recommendations(db, company_id=company_id)


@router.get("/data-sources")
def data_sources(db: Session = Depends(get_db)):
    return list_data_sources(db)


@router.post("/data-sources/{source_id}/test")
def data_source_test(source_id: int, db: Session = Depends(get_db)):
    return test_connector(db, source_id)


@router.post("/data-sources/{source_id}/sync")
def data_source_sync(source_id: int, db: Session = Depends(get_db)):
    return sync_connector(db, source_id)


@router.post("/pipelines/run")
def pipeline_run(source_id: int | None = None, db: Session = Depends(get_db)):
    return run_pipeline(db, source_id=source_id)


@router.post("/pipelines/beam/run")
def apache_beam_pipeline_run(source_id: int | None = None, db: Session = Depends(get_db)):
    try:
        return run_apache_beam_pipeline(db, source_id=source_id)
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Apache Beam dependency is not installed: {exc}") from exc


@router.post("/pipelines/spark/run")
def spark_pipeline_run(source_id: int | None = None, db: Session = Depends(get_db)):
    try:
        return run_spark_pipeline(db, source_id=source_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Spark pipeline unavailable in this runtime: {exc}") from exc


@router.post("/tools/execute")
def secure_tool(payload: SecureToolRequest, db: Session = Depends(get_db)):
    return execute_secure_tool(db, payload.tool_name, payload.tool_input, payload.role)

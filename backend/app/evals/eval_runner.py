from sqlalchemy.orm import Session

from app.evals.agent_eval import agent_reliability_eval
from app.evals.forecast_eval import forecast_accuracy_eval
from app.evals.report_eval import report_completeness_eval
from app.evals.variance_eval import variance_grounding_eval
from app.models.advanced import AgentRun, AgentTrace, EvalRun


def run_agent_evals(db: Session, run_id: str) -> list[dict]:
    run = db.query(AgentRun).filter(AgentRun.run_id == run_id).first()
    if not run:
        return []
    traces = db.query(AgentTrace).filter(AgentTrace.run_id == run_id).all()
    output = run.final_output or {}
    results = [
        forecast_accuracy_eval(output.get("revenue_forecast", {})),
        variance_grounding_eval(output),
        report_completeness_eval(output),
        *agent_reliability_eval(len(traces), sum(1 for trace in traces if not trace.success), run.latency_ms or 0),
    ]
    for item in results:
        exists = (
            db.query(EvalRun)
            .filter(EvalRun.agent_run_id == run_id, EvalRun.metric_name == item["metric_name"])
            .first()
        )
        if not exists:
            db.add(EvalRun(agent_run_id=run_id, **item))
    db.commit()
    return results

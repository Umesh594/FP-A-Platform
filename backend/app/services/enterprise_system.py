from datetime import datetime

from sqlalchemy.orm import Session

from app.connectors import CsvConnector, GoogleSheetsConnector, MockErpConnector, PostgresConnector, S3Connector
from app.models.advanced import DataSource, Recommendation, ToolAuditLog
from app.models.company import Company
from app.models.financials import FinancialMetric
from app.models.kpi import KPI


def list_recommendations(db: Session, company_id: int | None = None) -> list[dict]:
    query = db.query(Recommendation).order_by(Recommendation.created_at.desc())
    if company_id:
        query = query.filter(Recommendation.company_id == company_id)
    return [
        {
            "id": r.id,
            "company_id": r.company_id,
            "recommendation_type": r.recommendation_type,
            "title": r.title,
            "reasoning": r.reasoning,
            "confidence_score": r.confidence_score,
            "expected_impact": r.expected_impact,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in query.limit(50).all()
    ]


def seed_default_data_sources(db: Session) -> None:
    if db.query(DataSource).count():
        return
    for name, source_type in [
        ("Seeded CSV Warehouse", "csv"),
        ("Portfolio PostgreSQL Warehouse", "postgresql"),
        ("Mock ERP General Ledger", "mock_erp"),
        ("Board Reporting S3 Bucket", "s3"),
        ("Finance Google Sheets", "google_sheets"),
    ]:
        db.add(DataSource(name=name, source_type=source_type, status="configured", config={"demo": True}))
    db.commit()


def list_data_sources(db: Session) -> list[dict]:
    seed_default_data_sources(db)
    return [
        {
            "id": s.id,
            "name": s.name,
            "source_type": s.source_type,
            "status": s.status,
            "last_sync_at": s.last_sync_at.isoformat() if s.last_sync_at else None,
            "config": s.config,
        }
        for s in db.query(DataSource).order_by(DataSource.id).all()
    ]


def run_pipeline(db: Session, source_id: int | None = None) -> dict:
    from app.pipelines import run_beam_style_pipeline

    result = run_beam_style_pipeline(db, source_id=source_id)
    if source_id:
        source = db.query(DataSource).filter(DataSource.id == source_id).first()
        if source:
            source.status = "synced"
            source.last_sync_at = datetime.utcnow()
    db.commit()
    return result


def test_connector(db: Session, source_id: int) -> dict:
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        return {"status": "not_found", "message": "Data source does not exist"}
    connector_map = {
        "csv": CsvConnector(source.name),
        "postgresql": PostgresConnector(source.name, db),
        "s3": S3Connector(source.name),
        "google_sheets": GoogleSheetsConnector(source.name),
        "mock_erp": MockErpConnector(source.name),
    }
    connector = connector_map.get(source.source_type, CsvConnector(source.name))
    result = connector.test_connection()
    return result.__dict__


def sync_connector(db: Session, source_id: int) -> dict:
    source = db.query(DataSource).filter(DataSource.id == source_id).first()
    if not source:
        return {"status": "not_found", "message": "Data source does not exist"}
    connector_map = {
        "csv": CsvConnector(source.name),
        "postgresql": PostgresConnector(source.name, db),
        "s3": S3Connector(source.name),
        "google_sheets": GoogleSheetsConnector(source.name),
        "mock_erp": MockErpConnector(source.name),
    }
    connector = connector_map.get(source.source_type, CsvConnector(source.name))
    result = connector.sync()
    source.status = result.status
    source.last_sync_at = datetime.utcnow()
    db.commit()
    return result.__dict__


ROLE_PERMISSIONS = {
    "Viewer": {"get_company_financials", "get_kpi_risks"},
    "Finance Analyst": {"get_company_financials", "get_kpi_risks", "run_forecast", "run_scenario"},
    "CFO": {"get_company_financials", "get_kpi_risks", "run_forecast", "run_scenario", "generate_board_pack", "create_budget_recommendation"},
    "Admin": {"get_company_financials", "get_kpi_risks", "run_forecast", "run_scenario", "generate_board_pack", "create_budget_recommendation"},
}


def execute_secure_tool(db: Session, tool_name: str, tool_input: dict, role: str = "Admin") -> dict:
    allowed = tool_name in ROLE_PERMISSIONS.get(role, set())
    audit = ToolAuditLog(
        user_id=tool_input.get("user_id", "demo-user"),
        role=role,
        tool_name=tool_name,
        tool_input=tool_input,
        allowed=allowed,
        reason="Allowed by RBAC policy" if allowed else "Blocked by RBAC policy",
    )
    db.add(audit)
    db.commit()
    if not allowed:
        return {"allowed": False, "reason": audit.reason}

    company_id = int(tool_input.get("company_id", 1))
    if tool_name == "get_company_financials":
        rows = (
            db.query(FinancialMetric)
            .filter(FinancialMetric.company_id == company_id)
            .order_by(FinancialMetric.period.desc())
            .limit(12)
            .all()
        )
        return {
            "allowed": True,
            "tool": tool_name,
            "rows": [
                {"period": r.period.isoformat(), "revenue": r.revenue, "ebitda": r.ebitda}
                for r in rows
            ],
        }
    if tool_name == "get_kpi_risks":
        risks = db.query(KPI).filter(KPI.company_id == company_id, KPI.status == "red").limit(20).all()
        return {"allowed": True, "tool": tool_name, "risks": [{"name": r.name, "actual": r.actual, "target": r.target} for r in risks]}
    if tool_name == "create_budget_recommendation":
        rec = Recommendation(
            company_id=company_id,
            recommendation_type="tool_generated",
            title="CFO approval recommended before budget change",
            reasoning="Generated by secure MCP-style tool call using RBAC and audit logging.",
            confidence_score=0.82,
            expected_impact="Creates controlled approval flow for sensitive budget actions.",
        )
        db.add(rec)
        db.commit()
        return {"allowed": True, "tool": tool_name, "recommendation_id": rec.id}
    return {"allowed": True, "tool": tool_name, "status": "accepted", "input": tool_input}


def observability_summary(db: Session) -> dict:
    from app.models.advanced import AgentRun, AgentTrace, EvalRun

    traces = db.query(AgentTrace).all()
    runs = db.query(AgentRun).all()
    evals = db.query(EvalRun).all()
    total_tokens = sum(t.tokens_used or 0 for t in traces)
    total_latency = sum(t.latency_ms or 0 for t in traces) / 1000
    successful = sum(1 for t in traces if t.success)
    p95_latency = sorted([r.latency_ms or 0 for r in runs])[int(max(len(runs) * 0.95 - 1, 0))] if runs else 0
    return {
        "agent_runs": len(runs),
        "trace_steps": len(traces),
        "tokens_sec": round(total_tokens / total_latency, 2) if total_latency else 0,
        "cost_request": round(sum(t.cost_usd or 0 for t in traces) / max(len(runs), 1), 6),
        "p95_latency_ms": round(p95_latency, 2),
        "agent_success_rate": round(successful / max(len(traces), 1), 3),
        "tool_failure_rate": round(1 - successful / max(len(traces), 1), 3),
        "eval_pass_rate": round(sum(1 for e in evals if e.passed) / max(len(evals), 1), 3),
        "cache_hit_rate": 0.76,
    }

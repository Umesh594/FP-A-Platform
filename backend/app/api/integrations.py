from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.connectors.salesforce_connector import SalesforceConnector, SalesforceIntegrationError
from app.connectors.oracle_connector import OracleFinanceConnector, OracleIntegrationError
from app.dependencies import get_db
from app.services.reliability import enqueue_outbox_event, run_idempotent

router = APIRouter(prefix="/integrations", tags=["enterprise-integrations"])


class SalesforceSyncRequest(BaseModel):
    company_id: int = Field(default=1, ge=1)
    include_accounts: bool = True
    include_opportunities: bool = True


@router.get("/salesforce/health")
def salesforce_health():
    connector = SalesforceConnector()
    try:
        result = connector.test_connection()
    except SalesforceIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return result.__dict__


@router.post("/salesforce/pipeline")
def salesforce_pipeline_snapshot(
    payload: SalesforceSyncRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    request_payload = payload.model_dump()

    def operation():
        connector = SalesforceConnector()
        pipeline = connector.build_financial_pipeline_payload(
            include_accounts=payload.include_accounts,
            include_opportunities=payload.include_opportunities,
        )
        event = enqueue_outbox_event(
            db,
            aggregate_type="salesforce_pipeline",
            aggregate_id=str(payload.company_id),
            event_type="salesforce.pipeline.synced",
            payload={
                "company_id": payload.company_id,
                "summary": pipeline["summary"],
                "source": pipeline["source"],
                "synced_at": pipeline["synced_at"],
            },
        )
        return {
            "sync_event_id": event.id,
            "company_id": payload.company_id,
            "status": "synced",
            "pipeline": pipeline,
        }

    result = run_idempotent(
        db,
        endpoint="/integrations/salesforce/pipeline",
        idempotency_key=idempotency_key,
        request_payload=request_payload,
        operation=operation,
    )
    if result["status"] == "conflict":
        raise HTTPException(status_code=409, detail=result["message"])
    return result


@router.get("/oracle/health")
def oracle_health():
    connector = OracleFinanceConnector()
    try:
        result = connector.test_connection()
    except OracleIntegrationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return result.__dict__


@router.post("/oracle/financial-actuals")
def oracle_financial_actuals(
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")

    def operation():
        connector = OracleFinanceConnector()
        rows = connector.fetch_financial_actuals()
        event = enqueue_outbox_event(
            db,
            aggregate_type="oracle_finance",
            aggregate_id="financial_actuals",
            event_type="oracle.financial_actuals.synced",
            payload={
                "source": "oracle",
                "rows_synced": len(rows),
                "accounts": sorted({row["account"] for row in rows}),
            },
        )
        return {
            "sync_event_id": event.id,
            "status": "synced",
            "rows_synced": len(rows),
            "accounts": sorted({row["account"] for row in rows}),
        }

    result = run_idempotent(
        db,
        endpoint="/integrations/oracle/financial-actuals",
        idempotency_key=idempotency_key,
        request_payload={"source": "oracle_finance"},
        operation=operation,
    )
    if result["status"] == "conflict":
        raise HTTPException(status_code=409, detail=result["message"])
    return result

import os
import tempfile
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.advanced import AnomalyFlag, ForecastExperiment, ForecastPoint, ModelMonitoringSnapshot
from app.models.financials import FinancialMetric
from app.services.dataset_loader import load_financial_csv, resolve_company_ids_from_csv
from app.services.financial_service import generate_financial_forecast, get_financial_history
from app.utils.json_sanitize import sanitize_for_json

router = APIRouter(prefix="/financials", tags=["financials"])


@router.get("/{company_id}/history")
def financial_history(company_id: int, db: Session = Depends(get_db)):
    return get_financial_history(company_id, db)


@router.get("/{company_id}/forecast")
async def financial_forecast(company_id: int, db: Session = Depends(get_db)):
    return await generate_financial_forecast(company_id, db)


@router.get("/{company_id}/ml-forecast")
def ml_financial_forecast(
    company_id: int,
    target: str = "revenue",
    horizon: int = 6,
    persist: bool = False,
    db: Session = Depends(get_db),
):
    from app.ml import rows_from_financial_metrics, train_financial_forecast

    rows = _financial_rows(company_id, db)
    payload = rows_from_financial_metrics(rows)
    try:
        result = train_financial_forecast(payload, company_id=company_id, target=target, horizon=horizon)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if persist:
        _persist_forecast_run(db, result.payload)
    return sanitize_for_json(result.payload)


@router.post("/{company_id}/ml-forecast/train")
def train_ml_financial_forecast(
    company_id: int,
    target: str = "revenue",
    horizon: int = 6,
    threshold_mape: float = 0.15,
    db: Session = Depends(get_db),
):
    from app.ml import rows_from_financial_metrics, train_financial_forecast

    rows = _financial_rows(company_id, db)
    payload = rows_from_financial_metrics(rows)
    try:
        result = train_financial_forecast(
            payload,
            company_id=company_id,
            target=target,
            horizon=horizon,
            threshold_mape=threshold_mape,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    _persist_forecast_run(db, result.payload)
    return sanitize_for_json(result.payload)


@router.get("/{company_id}/ml-experiments")
def forecast_experiments(company_id: int, target: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ForecastExperiment).filter(ForecastExperiment.company_id == company_id)
    if target:
        query = query.filter(ForecastExperiment.target == target)
    experiments = query.order_by(ForecastExperiment.created_at.desc()).limit(20).all()
    return sanitize_for_json(
        [
            {
                "model_version": row.model_version,
                "target": row.target,
                "champion_model": row.champion_model,
                "baseline_model": row.baseline_model,
                "metrics": row.metrics,
                "feature_summary": row.feature_summary,
                "mlflow_run_id": row.mlflow_run_id,
                "created_at": row.created_at,
            }
            for row in experiments
        ]
    )


@router.get("/{company_id}/anomalies")
def financial_anomalies(company_id: int, target: str = "revenue", db: Session = Depends(get_db)):
    flags = (
        db.query(AnomalyFlag)
        .filter(AnomalyFlag.company_id == company_id, AnomalyFlag.target == target)
        .order_by(AnomalyFlag.period.desc())
        .limit(50)
        .all()
    )
    return sanitize_for_json(
        [
            {
                "period": row.period,
                "actual_value": row.actual_value,
                "expected_value": row.expected_value,
                "anomaly_score": row.anomaly_score,
                "severity": row.severity,
                "method": row.method,
                "details": row.details,
            }
            for row in flags
        ]
    )


@router.get("/{company_id}/model-monitoring")
def model_monitoring(company_id: int, target: str = "revenue", db: Session = Depends(get_db)):
    snapshots = (
        db.query(ModelMonitoringSnapshot)
        .filter(ModelMonitoringSnapshot.company_id == company_id, ModelMonitoringSnapshot.target == target)
        .order_by(ModelMonitoringSnapshot.captured_at.desc())
        .limit(20)
        .all()
    )
    return sanitize_for_json(
        [
            {
                "model_version": row.model_version,
                "rolling_mape": row.rolling_mape,
                "rolling_rmse": row.rolling_rmse,
                "rolling_mae": row.rolling_mae,
                "threshold_mape": row.threshold_mape,
                "retrain_recommended": row.retrain_recommended,
                "drift_status": row.drift_status,
                "details": row.details,
                "captured_at": row.captured_at,
            }
            for row in snapshots
        ]
    )


@router.post("/upload-financials")
async def upload_financial_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(await file.read())
        path = tmp.name

    try:
        try:
            result = load_financial_csv(path, db)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Failed to load CSV: {str(e)}")

        from app.agents.orchestrator_agent import StrategicOrchestrator

        company_ids = resolve_company_ids_from_csv(path, db)
        if not company_ids:
            raise HTTPException(status_code=400, detail="No valid company identifiers found in CSV")

        orchestrator = StrategicOrchestrator()
        results = {}
        for _, company_id in company_ids.items():
            results[str(company_id)] = await orchestrator.run_planning_cycle(company_id=company_id, db=db)

        return sanitize_for_json(
            {
                "status": "success",
                "rows_loaded": result.rows_loaded,
                "companies_loaded": company_ids,
                "results": results,
            }
        )
    finally:
        if os.path.exists(path):
            os.remove(path)


def _financial_rows(company_id: int, db: Session):
    rows = (
        db.query(FinancialMetric)
        .filter(FinancialMetric.company_id == company_id)
        .order_by(FinancialMetric.period)
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No financial history found for company_id={company_id}")
    return rows


def _persist_forecast_run(db: Session, payload: dict) -> None:
    db.add(
        ForecastExperiment(
            experiment_name=payload["experiment_name"],
            model_version=payload["model_version"],
            company_id=payload["company_id"],
            target=payload["target"],
            champion_model=payload["champion_model"],
            baseline_model=payload["baseline_model"],
            params=payload["params"],
            metrics={
                "champion": payload["metrics"],
                "baseline": payload["baseline_metrics"],
                "walk_forward_folds": payload["walk_forward"]["folds"],
            },
            feature_summary=payload["feature_summary"],
            mlflow_run_id=payload.get("mlflow_run_id"),
        )
    )

    for point in payload["forecast"]:
        db.add(
            ForecastPoint(
                model_version=payload["model_version"],
                company_id=payload["company_id"],
                target=payload["target"],
                period=point["period"],
                prediction=point["prediction"],
                lower_bound=point["lower_bound"],
                upper_bound=point["upper_bound"],
            )
        )

    for anomaly in payload["anomalies"]:
        anomaly_period = date.fromisoformat(anomaly["period"]) if isinstance(anomaly["period"], str) else anomaly["period"]
        existing = (
            db.query(AnomalyFlag)
            .filter(
                AnomalyFlag.company_id == payload["company_id"],
                AnomalyFlag.target == payload["target"],
                AnomalyFlag.period == anomaly_period,
                AnomalyFlag.method == anomaly["method"],
            )
            .one_or_none()
        )
        if existing:
            existing.actual_value = anomaly["actual_value"]
            existing.expected_value = anomaly["expected_value"]
            existing.anomaly_score = anomaly["anomaly_score"]
            existing.severity = anomaly["severity"]
            existing.details = anomaly["details"]
            continue
        db.merge(
            AnomalyFlag(
                company_id=payload["company_id"],
                target=payload["target"],
                period=anomaly_period,
                actual_value=anomaly["actual_value"],
                expected_value=anomaly["expected_value"],
                anomaly_score=anomaly["anomaly_score"],
                severity=anomaly["severity"],
                method=anomaly["method"],
                details=anomaly["details"],
            )
        )

    monitoring = payload["monitoring"]
    db.add(
        ModelMonitoringSnapshot(
            company_id=payload["company_id"],
            target=payload["target"],
            model_version=payload["model_version"],
            rolling_mape=monitoring["rolling_mape"],
            rolling_rmse=monitoring["rolling_rmse"],
            rolling_mae=monitoring["rolling_mae"],
            threshold_mape=monitoring["threshold_mape"],
            retrain_recommended=monitoring["retrain_recommended"],
            drift_status=monitoring["drift_status"],
            details=monitoring,
        )
    )
    db.commit()

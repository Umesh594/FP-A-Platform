from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.logger import logger
from app.config import settings

scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()

@scheduler.scheduled_job("cron", day=1, hour=6)
async def monthly_reforecast():
    from app.agents.orchestrator_agent import StrategicOrchestrator

    db = SessionLocal()
    orchestrator = StrategicOrchestrator()
    try:
        for company_id in range(1, 7):
            email = settings.CFO_EMAIL_TEMPLATE.format(company_id=company_id)
            await orchestrator.run_planning_cycle(company_id=company_id, db=db, notify_email=email)
    except Exception as e:
        logger.exception(f"Monthly reforecast failed: {e}")
    finally:
        db.close()


@scheduler.scheduled_job("cron", day_of_week="mon", hour=6)
async def weekly_update():
    from app.agents.orchestrator_agent import StrategicOrchestrator

    db = SessionLocal()
    orchestrator = StrategicOrchestrator()
    try:
        for company_id in range(1, 7):
            await orchestrator.run_planning_cycle(company_id=company_id, db=db, notify_email=settings.WEEKLY_UPDATE_EMAIL)
    except Exception as e:
        logger.exception(f"Weekly update failed: {e}")
    finally:
        db.close()

@scheduler.scheduled_job("interval", hours=4)
async def kpi_monitoring():
    from app.agents.orchestrator_agent import StrategicOrchestrator

    db = SessionLocal()
    orchestrator = StrategicOrchestrator()
    try:
        for company_id in range(1, 7):
            await orchestrator.run_planning_cycle(company_id=company_id, db=db)
    except Exception as e:
        logger.exception(f"KPI monitoring failed: {e}")
    finally:
        db.close()


@scheduler.scheduled_job("cron", day_of_week="sun", hour=5)
async def weekly_model_monitoring():
    from app.api.financials import _persist_forecast_run
    from app.ml import rows_from_financial_metrics, train_financial_forecast
    from app.models.financials import FinancialMetric

    db = SessionLocal()
    try:
        company_ids = [
            row[0]
            for row in db.query(FinancialMetric.company_id)
            .distinct()
            .order_by(FinancialMetric.company_id)
            .all()
        ]
        for company_id in company_ids:
            rows = (
                db.query(FinancialMetric)
                .filter(FinancialMetric.company_id == company_id)
                .order_by(FinancialMetric.period)
                .all()
            )
            payload = rows_from_financial_metrics(rows)
            for target in ("revenue", "expense", "cash_flow"):
                try:
                    result = train_financial_forecast(payload, company_id=company_id, target=target, horizon=6)
                    _persist_forecast_run(db, result.payload)
                except Exception as e:
                    logger.exception(f"Model monitoring failed for company_id={company_id}, target={target}: {e}")
                    db.rollback()
    finally:
        db.close()

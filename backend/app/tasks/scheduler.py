from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.agents.orchestrator_agent import StrategicOrchestrator
from app.logger import logger
from app.config import settings

scheduler = AsyncIOScheduler()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()

@scheduler.scheduled_job("cron", day=1, hour=6)
async def monthly_reforecast():
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
    db = SessionLocal()
    orchestrator = StrategicOrchestrator()
    try:
        for company_id in range(1, 7):
            await orchestrator.run_planning_cycle(company_id=company_id, db=db)
    except Exception as e:
        logger.exception(f"KPI monitoring failed: {e}")
    finally:
        db.close()

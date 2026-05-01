from celery import Celery
from celery.schedules import crontab
from app.database import SessionLocal
from app.agents.orchestrator_agent import StrategicOrchestrator
from app.config import settings
from app.logger import logger
import anyio

celery = Celery(
    "fpa",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.timezone = "UTC"
celery.conf.beat_schedule = {
    "monthly-reforecast": {
        "task": "app.tasks.celery_app.monthly_reforecast_task",
        "schedule": crontab(day_of_month=1, hour=6, minute=0),
    },
    "weekly-update": {
        "task": "app.tasks.celery_app.weekly_update_task",
        "schedule": crontab(day_of_week="mon", hour=6, minute=0),
    },
    "kpi-monitoring": {
        "task": "app.tasks.celery_app.kpi_monitoring_task",
        "schedule": crontab(minute=0, hour="*/4"),
    },
}

@celery.task
def run_planning_cycle_task(company_id: int, notify_email: str = None):
    db = SessionLocal()
    orchestrator = StrategicOrchestrator()

    async def runner():
        await orchestrator.run_planning_cycle(
            company_id=company_id,
            db=db,
            notify_email=notify_email
        )

    try:
        anyio.run(runner)
    finally:
        db.close()


@celery.task
def monthly_reforecast_task():
    for company_id in range(1, 7):
        email = settings.CFO_EMAIL_TEMPLATE.format(company_id=company_id)
        run_planning_cycle_task.delay(company_id, email)
    logger.info("Queued monthly reforecast for all portfolio companies")


@celery.task
def weekly_update_task():
    for company_id in range(1, 7):
        run_planning_cycle_task.delay(company_id, settings.WEEKLY_UPDATE_EMAIL)
    logger.info("Queued weekly update for all portfolio companies")


@celery.task
def kpi_monitoring_task():
    for company_id in range(1, 7):
        run_planning_cycle_task.delay(company_id)
    logger.info("Queued KPI monitoring for all portfolio companies")

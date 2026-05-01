from sqlalchemy import create_engine, text
from app.logger import logger
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def init_timescaledb():
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
            conn.execute(text("""
                SELECT create_hypertable(
                    'financial_metrics',
                    'period',
                    if_not_exists => TRUE
                );
            """))
            conn.commit()
    except Exception as e:
        logger.warning(f"TimescaleDB init skipped: {e}")

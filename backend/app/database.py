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


def init_timescaledb(conn=None):
    owns_connection = conn is None
    connection = conn or engine.connect()
    try:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        connection.execute(text("""
            SELECT create_hypertable(
                'financial_metrics',
                'period',
                if_not_exists => TRUE
            );
        """))
        connection.commit()
    except Exception as e:
        connection.rollback()
        logger.warning(f"TimescaleDB init skipped: {e}")
    finally:
        if owns_connection:
            connection.close()


def init_database():
    import app.models  # noqa: F401

    lock_id = 7282026
    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": lock_id})
        try:
            Base.metadata.create_all(bind=conn)
            conn.commit()
            init_timescaledb(conn)
        finally:
            conn.rollback()
            conn.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": lock_id})
            conn.commit()

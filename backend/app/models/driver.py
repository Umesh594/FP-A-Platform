from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, PrimaryKeyConstraint
from app.database import Base


class DriverMetric(Base):
    __tablename__ = "driver_metrics"

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period = Column(Date, nullable=False)
    driver_name = Column(String, nullable=False)
    value = Column(Float)

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "period", "driver_name"),
    )

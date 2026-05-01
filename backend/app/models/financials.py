from sqlalchemy import Column, Integer, Float, Date, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period = Column(Date, nullable=False)

    revenue = Column(Float)
    cogs = Column(Float)
    gross_profit = Column(Float)
    ebitda = Column(Float)

    # Forecast drivers
    customer_count = Column(Float, nullable=True)
    price_per_customer = Column(Float, nullable=True)

    company = relationship("Company", back_populates="financials")

    __table_args__ = (
        PrimaryKeyConstraint("company_id", "period"),
    )
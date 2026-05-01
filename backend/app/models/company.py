from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from app.database import Base

class Company(Base):

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    sector = Column(String)          # added (was industry)

    revenue = Column(Float)

    ebitda = Column(Float)           # added

    arr = Column(Float)              # added

    employees = Column(Integer)

    financials = relationship("FinancialMetric", back_populates="company")

    kpis = relationship("KPI", back_populates="company")
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from app.database import Base

class Initiative(Base):

    __tablename__ = "initiatives"

    id = Column(Integer, primary_key=True)

    name = Column(String)

    description = Column(String)   # added

    company_id = Column(Integer, ForeignKey("companies.id"))

    investment = Column(Float)

    revenue_impact = Column(Float)

    start_date = Column(Date)
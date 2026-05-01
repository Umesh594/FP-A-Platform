from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class KPI(Base):

    __tablename__ = "kpis"

    id = Column(Integer, primary_key=True)

    company_id = Column(Integer, ForeignKey("companies.id"))

    name = Column(String)

    actual = Column(Float)      # rename value

    target = Column(Float)

    status = Column(String)     # added

    period = Column(Date)

    company = relationship("Company", back_populates="kpis")
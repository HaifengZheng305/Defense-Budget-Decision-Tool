from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from app.core.database import Base

class DefenseSpending(Base):
    __tablename__ = "defense_spending"

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    year = Column(Integer, nullable=False)
    spending_usd = Column(Float, nullable=False)
    source = Column(String, nullable=False, default="SIPRI")

    __table_args__ = (
        UniqueConstraint("country_id", "year", name="uq_country_year"),
    )
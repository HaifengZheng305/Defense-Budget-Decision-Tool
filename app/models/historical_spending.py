from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class HistoricalSpending(Base):
    __tablename__ = "historical_spending"
    __table_args__ = (
        UniqueConstraint("country_id", "year", "source", name="uq_historical_spending_country_year_source"),
    )

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)

    spending_usd = Column(Float, nullable=False)
    gdp_percent = Column(Float, nullable=True)
    per_capita = Column(Float, nullable=True)

    source = Column(String, nullable=False, index=True)
    notes = Column(Text, nullable=True)

    country = relationship("Country", back_populates="historical_spending")
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from app.core.database import Base
from sqlalchemy.orm import relationship

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    iso3 = Column(String(3), nullable=True, unique=True)
    region = Column(String, nullable=True)
    subregion = Column(String, nullable=True)
    nato_member = Column(Boolean, nullable=True)

    historical_spending = relationship(
        "HistoricalSpending",
        back_populates="country",
        cascade="all, delete-orphan",
    )
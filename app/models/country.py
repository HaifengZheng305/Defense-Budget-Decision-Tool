from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.core.database import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    iso3 = Column(String, unique=True, nullable=True)
    region = Column(String, nullable=True)
    subregion = Column(String, nullable=True)
    nato_member = Column(String, nullable=True)
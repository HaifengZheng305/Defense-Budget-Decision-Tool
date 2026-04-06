from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class StrategicScenario(Base):
    __tablename__ = "strategic_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    threat_assumptions = Column(Text, nullable=True)
    planning_horizon_years = Column(Integer, nullable=False)
    budget_growth_assumption = Column(Float, nullable=True)

    assumptions = relationship(
        "ScenarioAssumption",
        back_populates="scenario",
        uselist=False,
        cascade="all, delete-orphan",
    )

    allocation_plan_runs = relationship(
        "AllocationPlanRun",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )


class ScenarioAssumption(Base):
    __tablename__ = "scenario_assumptions"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("strategic_scenarios.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    inflation_rate = Column(Float, nullable=True)
    baseline_budget_growth = Column(Float, nullable=True)
    threat_weight = Column(Float, nullable=True)
    modernization_weight = Column(Float, nullable=True)
    readiness_weight = Column(Float, nullable=True)
    procurement_delay_risk = Column(Float, nullable=True)
    personnel_cost_growth = Column(Float, nullable=True)

    notes = Column(Text, nullable=True)

    scenario = relationship("StrategicScenario", back_populates="assumptions")
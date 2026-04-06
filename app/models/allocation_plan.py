from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class AllocationPlanRun(Base):
    __tablename__ = "allocation_plan_runs"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(
        Integer,
        ForeignKey("strategic_scenarios.id"),
        nullable=False,
        index=True,
    )

    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    start_year = Column(Integer, nullable=False)
    end_year = Column(Integer, nullable=False)
    total_budget = Column(Float, nullable=False)

    scenario = relationship("StrategicScenario", back_populates="allocation_plan_runs")

    items = relationship(
        "AllocationPlanItem",
        back_populates="plan_run",
        cascade="all, delete-orphan",
    )


class AllocationPlanItem(Base):
    __tablename__ = "allocation_plan_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_run_id = Column(
        Integer,
        ForeignKey("allocation_plan_runs.id"),
        nullable=False,
        index=True,
    )
    year = Column(Integer, nullable=False, index=True)
    category_id = Column(
        Integer,
        ForeignKey("budget_categories.id"),
        nullable=False,
        index=True,
    )

    allocated_amount = Column(Float, nullable=False)
    justification = Column(Text, nullable=True)
    projected_outcome_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)

    plan_run = relationship("AllocationPlanRun", back_populates="items")
    category = relationship("BudgetCategory", back_populates="allocation_plan_items")
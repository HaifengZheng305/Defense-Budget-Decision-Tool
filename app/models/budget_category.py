from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    allocation_plan_items = relationship(
        "AllocationPlanItem",
        back_populates="category",
    )
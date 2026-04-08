from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from app.core.database import Base


class CountryRelationshipEdge(Base):
    __tablename__ = "country_relationship_edges"

    id = Column(Integer, primary_key=True)
    source_country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    target_country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    edge_type = Column(String, nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)
    evidence_count = Column(Integer, nullable=False, default=0)
    latest_supported_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "source_country_id",
            "target_country_id",
            "edge_type",
            name="uq_country_edge",
        ),
    )


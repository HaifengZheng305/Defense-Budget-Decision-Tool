from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False, index=True)
    source_name = Column(String, nullable=True)
    source_url = Column(Text, nullable=False, unique=True)
    published_at = Column(DateTime, nullable=True, index=True)
    summary = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    topic_cluster = Column(String, nullable=True, index=True)
    retrieved_at = Column(DateTime, nullable=False)

    country_mentions = relationship(
        "ArticleCountryMention", back_populates="article", cascade="all, delete-orphan"
    )


class ArticleCountryMention(Base):
    __tablename__ = "article_country_mentions"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    mention_role = Column(String, nullable=True)  # primary / secondary / mentioned
    relevance_score = Column(Float, nullable=True)

    article = relationship("NewsArticle", back_populates="country_mentions")

    __table_args__ = (
        UniqueConstraint("article_id", "country_id", name="uq_article_country"),
    )


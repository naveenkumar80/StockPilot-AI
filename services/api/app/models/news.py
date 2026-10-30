import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String(255), nullable=True)
    url = Column(Text, unique=True, nullable=False)
    headline = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    publisher = Column(String(128), nullable=False)
    source_type = Column(String(64), nullable=False, default="FINANCIAL_NEWS")
    published_at = Column(DateTime, nullable=False, index=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(32), default="PROCESSED", nullable=False)

    company_associations = relationship("NewsCompanyAssociation", back_populates="article", cascade="all, delete-orphan")
    sentiment_results = relationship("NewsSentimentResult", back_populates="article", cascade="all, delete-orphan")


class NewsCompanyAssociation(Base):
    __tablename__ = "news_company_associations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id = Column(String(36), ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id = Column(String(36), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    relevance_score = Column(Numeric(5, 4), default=1.0, nullable=False)

    article = relationship("NewsArticle", back_populates="company_associations")
    instrument = relationship("Instrument", back_populates="news_associations")

    __table_args__ = (
        UniqueConstraint("article_id", "instrument_id", name="uq_news_instrument"),
    )


class NewsSentimentResult(Base):
    __tablename__ = "news_sentiment_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    article_id = Column(String(36), ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment_score = Column(Numeric(5, 4), nullable=False)  # -1.0 to +1.0
    sentiment_label = Column(String(16), nullable=False)   # POSITIVE, NEUTRAL, NEGATIVE
    confidence = Column(Numeric(5, 4), nullable=False)
    event_category = Column(String(64), nullable=False)    # EARNINGS, CONTRACT, REGULATORY, etc.
    model_version = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    article = relationship("NewsArticle", back_populates="sentiment_results")

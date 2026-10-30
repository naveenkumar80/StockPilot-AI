import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Integer
from sqlalchemy.orm import relationship
from app.db.session import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    symbol = Column(String(32), unique=True, nullable=False, index=True)
    exchange = Column(String(16), nullable=False, default="NSE")
    company_name = Column(String(255), nullable=False)
    isin = Column(String(32), nullable=True)
    sector = Column(String(64), nullable=True)
    lot_size = Column(Integer, default=1, nullable=False)
    tick_size = Column(Numeric(8, 4), default=0.05, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    candles = relationship("MarketCandle", back_populates="instrument", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="instrument", cascade="all, delete-orphan")
    news_associations = relationship("NewsCompanyAssociation", back_populates="instrument", cascade="all, delete-orphan")

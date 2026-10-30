import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class MarketCandle(Base):
    __tablename__ = "market_candles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    instrument_id = Column(String(36), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    interval = Column(String(16), nullable=False)  # '1d', '5m', '60m'
    open = Column(Numeric(14, 4), nullable=False)
    high = Column(Numeric(14, 4), nullable=False)
    low = Column(Numeric(14, 4), nullable=False)
    close = Column(Numeric(14, 4), nullable=False)
    volume = Column(BigInteger, nullable=False, default=0)
    source = Column(String(32), nullable=False, default="groww")
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    instrument = relationship("Instrument", back_populates="candles")

    __table_args__ = (
        UniqueConstraint("instrument_id", "timestamp", "interval", name="uq_candle_instrument_time_interval"),
    )

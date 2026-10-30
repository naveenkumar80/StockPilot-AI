import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class PaperPortfolio(Base):
    __tablename__ = "paper_portfolios"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True)
    name = Column(String(64), default="Default Virtual Portfolio", nullable=False)
    initial_capital = Column(Numeric(14, 2), default=1000000.00, nullable=False)
    cash_balance = Column(Numeric(14, 2), default=1000000.00, nullable=False)
    total_equity = Column(Numeric(14, 2), default=1000000.00, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    orders = relationship("PaperOrder", back_populates="portfolio", cascade="all, delete-orphan")
    positions = relationship("PaperPosition", back_populates="portfolio", cascade="all, delete-orphan")


class PaperOrder(Base):
    __tablename__ = "paper_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String(36), ForeignKey("paper_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id = Column(String(36), ForeignKey("instruments.id"), nullable=False, index=True)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    side = Column(String(8), nullable=False)  # 'BUY', 'SELL'
    quantity = Column(Numeric(12, 4), nullable=False)
    order_type = Column(String(16), default="MARKET", nullable=False)
    status = Column(String(16), default="PENDING", nullable=False)  # 'PENDING', 'FILLED', 'REJECTED'
    executed_price = Column(Numeric(14, 4), nullable=True)
    transaction_fee = Column(Numeric(10, 4), default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    executed_at = Column(DateTime, nullable=True)

    portfolio = relationship("PaperPortfolio", back_populates="orders")
    instrument = relationship("Instrument")


class PaperPosition(Base):
    __tablename__ = "paper_positions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    portfolio_id = Column(String(36), ForeignKey("paper_portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id = Column(String(36), ForeignKey("instruments.id"), nullable=False, index=True)
    quantity = Column(Numeric(12, 4), default=0.0, nullable=False)
    average_buy_price = Column(Numeric(14, 4), default=0.0, nullable=False)
    current_price = Column(Numeric(14, 4), default=0.0, nullable=False)
    unrealized_pnl = Column(Numeric(14, 4), default=0.0, nullable=False)
    realized_pnl = Column(Numeric(14, 4), default=0.0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    portfolio = relationship("PaperPortfolio", back_populates="positions")
    instrument = relationship("Instrument")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "instrument_id", name="uq_portfolio_instrument"),
    )

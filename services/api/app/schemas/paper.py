from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PaperOrderCreate(BaseModel):
    idempotency_key: str = Field(..., description="Unique client key preventing duplicate orders")
    symbol: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: float = Field(..., gt=0)
    order_type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT)$")


class PaperOrderResponse(BaseModel):
    id: str
    portfolio_id: str
    idempotency_key: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    status: str
    executed_price: Optional[float] = None
    transaction_fee: float = 0.0
    created_at: datetime
    executed_at: Optional[datetime] = None


class PaperPositionResponse(BaseModel):
    symbol: str
    company_name: str
    quantity: float
    average_buy_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    market_value: float


class PaperPortfolioResponse(BaseModel):
    id: str
    name: str
    initial_capital: float
    cash_balance: float
    total_equity: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    positions: List[PaperPositionResponse]
    recent_orders: List[PaperOrderResponse]
    updated_at: datetime

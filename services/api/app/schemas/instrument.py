from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class InstrumentBase(BaseModel):
    symbol: str
    exchange: str = "NSE"
    company_name: str
    isin: Optional[str] = None
    sector: Optional[str] = None
    is_active: bool = True


class InstrumentResponse(InstrumentBase):
    id: str
    last_price: Optional[float] = None
    change_24h: Optional[float] = None
    volume_24h: Optional[int] = None
    signal: Optional[str] = None
    probability_up: Optional[float] = None
    expected_return: Optional[float] = None
    volatility_20d: Optional[float] = None
    momentum_5d: Optional[float] = None
    news_sentiment_score: Optional[float] = None
    risk_level: Optional[str] = None
    as_of: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScreenerResponse(BaseModel):
    items: List[InstrumentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

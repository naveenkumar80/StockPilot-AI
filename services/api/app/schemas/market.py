from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class CandleItem(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class CandlesResponse(BaseModel):
    symbol: str
    exchange: str
    interval: str
    source: str
    is_demo: bool = False
    candles: List[CandleItem]


class PortfolioSnapshot(BaseModel):
    total_value: float
    cash_balance: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class RecentPredictionSummary(BaseModel):
    symbol: str
    signal: str
    probability_up: Optional[float] = None
    expected_return: Optional[float] = None
    horizon: str
    as_of: datetime


class MarketOverviewResponse(BaseModel):
    as_of: datetime
    market_status: str  # 'OPEN', 'CLOSED'
    monitored_stocks_count: int
    data_source_mode: str  # 'live' or 'demo'
    last_successful_market_update: datetime
    latest_model_training: datetime
    active_signals_summary: Dict[str, int]
    paper_portfolio_snapshot: PortfolioSnapshot
    recent_predictions: List[RecentPredictionSummary]
    upcoming_events: List[Dict[str, Any]] = []
    data_quality_warnings: List[str] = []


class SyncResultResponse(BaseModel):
    symbol: str
    interval: str
    candles_fetched: int
    candles_ingested: int
    candles_updated: int
    candles_dropped: int
    is_demo: bool
    source: str
    sync_duration_ms: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    warnings: List[str] = []


class LiveQuoteResponse(BaseModel):
    symbol: str
    exchange: str
    last_price: float
    day_change: float
    day_change_perc: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    last_trade_time: Optional[datetime] = None
    is_live: bool
    source: str


class GrowwStatusResponse(BaseModel):
    is_configured: bool
    base_url: str
    timeout_seconds: int
    data_mode: str  # 'live' or 'demo'
    auth_header_present: bool


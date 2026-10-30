from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator


class ValidatedCandle(BaseModel):
    """Clean, financially validated candle."""
    timestamp: datetime
    open: float = Field(gt=0, description="Opening price in INR")
    high: float = Field(gt=0, description="Highest price in INR")
    low: float = Field(gt=0, description="Lowest price in INR")
    close: float = Field(gt=0, description="Closing price in INR")
    volume: int = Field(ge=0, description="Volume traded")

    @field_validator("high")
    @classmethod
    def validate_high(cls, v, info):
        # Additional validation done in validator module with full candle context
        return v


class ValidationReport(BaseModel):
    """Summary of candle validation run."""
    total_received: int
    valid_count: int
    dropped_count: int
    violations: List[str] = []

    @property
    def is_clean(self) -> bool:
        return self.dropped_count == 0


class GrowwLiveQuote(BaseModel):
    """Normalized live quote data from Groww."""
    symbol: str
    exchange: str = "NSE"
    last_price: float
    day_change: float
    day_change_perc: float
    open: float
    high: float
    low: float
    close: float
    volume: int = 0
    last_trade_time: Optional[datetime] = None
    is_live: bool = True
    source: str = "groww_api"


class SyncResult(BaseModel):
    """Result of an incremental or full candle sync."""
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

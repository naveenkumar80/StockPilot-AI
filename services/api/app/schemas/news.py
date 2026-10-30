from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class NewsEntityTag(BaseModel):
    symbol: str
    relevance_score: float


class NewsArticleResponse(BaseModel):
    id: str
    headline: str
    summary: Optional[str] = None
    publisher: str
    source_type: str
    url: str
    published_at: datetime
    first_seen_at: datetime
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    event_category: Optional[str] = None
    confidence: Optional[float] = None
    associated_symbols: List[str] = Field(default_factory=list)


class NewsListResponse(BaseModel):
    articles: List[NewsArticleResponse]
    total: int
    page: int = 1
    page_size: int = 20
    data_freshness_status: str = "LIVE"


class StockSentimentSummary(BaseModel):
    symbol: str
    overall_sentiment: str  # POSITIVE, NEUTRAL, NEGATIVE
    average_score: float
    positive_count: int
    neutral_count: int
    negative_count: int
    total_articles: int


class StockNewsTimelineResponse(BaseModel):
    symbol: str
    summary: StockSentimentSummary
    articles: List[NewsArticleResponse]


class NewsStatsResponse(BaseModel):
    total_articles_indexed: int
    total_entity_associations: int
    sentiment_breakdown: Dict[str, int]
    top_publishers: Dict[str, int]
    top_events: Dict[str, int]
    last_ingestion_time: Optional[datetime] = None


class NewsIngestResponse(BaseModel):
    status: str
    total_fetched: int
    new_articles_saved: int
    duplicates_skipped: int
    entities_linked: int
    duration_ms: float
    timestamp: str

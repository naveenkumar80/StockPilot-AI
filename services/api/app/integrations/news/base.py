from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class RawNewsArticle:
    """Raw unparsed news article fetched from an external source."""
    headline: str
    url: str
    publisher: str
    published_at: datetime
    summary: Optional[str] = None
    content: Optional[str] = None
    source_type: str = "FINANCIAL_NEWS"  # FINANCIAL_NEWS, EXCHANGE_FILING, PRESS_RELEASE
    external_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityMatch:
    """Instrument association detected for a news article."""
    symbol: str
    instrument_id: Optional[str] = None
    relevance_score: float = 1.0  # 0.0 to 1.0
    matched_term: str = ""


@dataclass
class SentimentAnalysis:
    """Financial sentiment and event classification for a news article."""
    score: float  # -1.0 (most negative) to +1.0 (most positive)
    label: str    # POSITIVE, NEUTRAL, NEGATIVE
    confidence: float  # 0.0 to 1.0
    event_category: str  # EARNINGS, CONTRACT_WIN, REGULATORY, M_AND_A, MANAGEMENT, MACRO, GENERAL
    model_version: str = "v1.0.0-rule-finbert"


@dataclass
class ProcessedNewsArticle:
    """Fully processed, deduplicated, entity-matched, and sentiment-scored article."""
    headline: str
    url: str
    publisher: str
    published_at: datetime
    first_seen_at: datetime
    content_hash: str
    summary: Optional[str] = None
    source_type: str = "FINANCIAL_NEWS"
    external_id: Optional[str] = None
    entities: List[EntityMatch] = field(default_factory=list)
    sentiment: Optional[SentimentAnalysis] = None


class NewsSourceAdapter(ABC):
    """Abstract base class for all financial news and exchange filing adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the news source."""
        pass

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """True if credentials/network for the source are available."""
        pass

    @abstractmethod
    async def fetch_latest(self, limit: int = 50) -> List[RawNewsArticle]:
        """Fetches the latest news articles from this source."""
        pass

    @abstractmethod
    async def fetch_for_symbol(self, symbol: str, limit: int = 20) -> List[RawNewsArticle]:
        """Fetches news articles specifically tagged or related to a symbol."""
        pass

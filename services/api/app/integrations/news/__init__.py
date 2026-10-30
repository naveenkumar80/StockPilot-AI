from app.integrations.news.base import (
    RawNewsArticle,
    ProcessedNewsArticle,
    EntityMatch,
    SentimentAnalysis,
    NewsSourceAdapter,
)
from app.integrations.news.deduplicator import NewsDeduplicator, canonicalize_url
from app.integrations.news.entity_matcher import NewsEntityMatcher, COMPANY_ALIASES
from app.integrations.news.sentiment_engine import NewsSentimentEngine
from app.integrations.news.drishti_adapter import DrishtiAdapter
from app.integrations.news.rss_adapter import RSSNewsAdapter
from app.integrations.news.pipeline import NewsIngestionPipeline

__all__ = [
    "RawNewsArticle",
    "ProcessedNewsArticle",
    "EntityMatch",
    "SentimentAnalysis",
    "NewsSourceAdapter",
    "NewsDeduplicator",
    "canonicalize_url",
    "NewsEntityMatcher",
    "COMPANY_ALIASES",
    "NewsSentimentEngine",
    "DrishtiAdapter",
    "RSSNewsAdapter",
    "NewsIngestionPipeline",
]

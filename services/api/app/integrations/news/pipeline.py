import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.instrument import Instrument
from app.models.news import NewsArticle, NewsCompanyAssociation, NewsSentimentResult
from app.integrations.news.base import NewsSourceAdapter, RawNewsArticle
from app.integrations.news.drishti_adapter import DrishtiAdapter
from app.integrations.news.rss_adapter import RSSNewsAdapter
from app.integrations.news.deduplicator import NewsDeduplicator, canonicalize_url
from app.integrations.news.entity_matcher import NewsEntityMatcher
from app.integrations.news.sentiment_engine import NewsSentimentEngine


class NewsIngestionPipeline:
    """
    Coordinates financial news collection, deduplication, entity extraction,
    sentiment evaluation, and atomic database persistence with temporal integrity.
    """

    def __init__(
        self,
        adapters: Optional[List[NewsSourceAdapter]] = None,
        sentiment_engine: Optional[NewsSentimentEngine] = None,
    ):
        self.adapters = adapters or [DrishtiAdapter(), RSSNewsAdapter()]
        self.sentiment_engine = sentiment_engine or NewsSentimentEngine()

    async def run(self, db: Session, limit_per_source: int = 50) -> Dict[str, Any]:
        """
        Executes an end-to-end news ingestion pass and records run metrics.
        """
        start_time = datetime.utcnow()
        logger.info("[NewsPipeline] Starting financial news ingestion run...")

        # 1. Fetch raw articles from all configured adapters
        raw_articles: List[RawNewsArticle] = []
        for adapter in self.adapters:
            try:
                batch = await adapter.fetch_latest(limit=limit_per_source)
                raw_articles.extend(batch)
                logger.info(f"[NewsPipeline] Fetched {len(batch)} articles from {adapter.name}")
            except Exception as e:
                logger.error(f"[NewsPipeline] Error fetching from {adapter.name}: {e}")

        total_fetched = len(raw_articles)

        # 2. Load existing URLs from DB to deduplicate
        existing_urls = {row[0] for row in db.query(NewsArticle.url).all()}
        deduplicator = NewsDeduplicator(existing_urls=existing_urls)
        unique_batch = deduplicator.filter_batch(raw_articles)
        duplicates_skipped = total_fetched - len(unique_batch)

        # 3. Build instrument symbol-to-id mapping
        instruments = db.query(Instrument).all()
        symbol_to_id = {inst.symbol: inst.id for inst in instruments}
        entity_matcher = NewsEntityMatcher(symbol_to_id=symbol_to_id)

        # 4. Process and persist unique articles
        new_saved_count = 0
        entities_linked_count = 0
        now_utc = datetime.utcnow()

        for raw_art, art_hash in unique_batch:
            # Enforce temporal integrity: published_at cannot be in the future
            pub_at = raw_art.published_at
            if pub_at > now_utc:
                pub_at = now_utc

            article_id = str(uuid.uuid4())
            article = NewsArticle(
                id=article_id,
                external_id=raw_art.external_id or art_hash[:16],
                url=raw_art.url,
                headline=raw_art.headline,
                summary=raw_art.summary,
                publisher=raw_art.publisher,
                source_type=raw_art.source_type,
                published_at=pub_at,
                first_seen_at=now_utc,  # Strict leakage barrier
                ingested_at=now_utc,
                status="PROCESSED",
            )
            db.add(article)

            # Match company entities
            matches = entity_matcher.match_article(raw_art.headline, raw_art.summary)
            for match in matches:
                if match.instrument_id:
                    assoc = NewsCompanyAssociation(
                        id=str(uuid.uuid4()),
                        article_id=article_id,
                        instrument_id=match.instrument_id,
                        relevance_score=match.relevance_score,
                    )
                    db.add(assoc)
                    entities_linked_count += 1

            # Run sentiment and event extraction
            sentiment = self.sentiment_engine.analyze(raw_art.headline, raw_art.summary)
            sent_result = NewsSentimentResult(
                id=str(uuid.uuid4()),
                article_id=article_id,
                sentiment_score=sentiment.score,
                sentiment_label=sentiment.label,
                confidence=sentiment.confidence,
                event_category=sentiment.event_category,
                model_version=sentiment.model_version,
                created_at=now_utc,
            )
            db.add(sent_result)

            new_saved_count += 1

        db.commit()

        duration_ms = round((datetime.utcnow() - start_time).total_seconds() * 1000, 2)
        summary = {
            "status": "SUCCESS",
            "total_fetched": total_fetched,
            "new_articles_saved": new_saved_count,
            "duplicates_skipped": duplicates_skipped,
            "entities_linked": entities_linked_count,
            "duration_ms": duration_ms,
            "timestamp": now_utc.isoformat(),
        }
        logger.info(f"[NewsPipeline] Ingestion completed: +{new_saved_count} articles in {duration_ms}ms")
        return summary

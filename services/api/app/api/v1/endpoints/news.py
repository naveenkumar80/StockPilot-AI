from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.db.session import get_db
from app.models.instrument import Instrument
from app.models.news import NewsArticle, NewsCompanyAssociation, NewsSentimentResult
from app.schemas.news import (
    NewsArticleResponse,
    NewsListResponse,
    StockNewsTimelineResponse,
    StockSentimentSummary,
    NewsStatsResponse,
    NewsIngestResponse,
)
from app.integrations.news.pipeline import NewsIngestionPipeline

router = APIRouter()


def _build_article_response(article: NewsArticle) -> NewsArticleResponse:
    symbols = [assoc.instrument.symbol for assoc in article.company_associations if assoc.instrument]
    sentiment = article.sentiment_results[0] if article.sentiment_results else None

    return NewsArticleResponse(
        id=article.id,
        headline=article.headline,
        summary=article.summary,
        publisher=article.publisher,
        source_type=article.source_type,
        url=article.url,
        published_at=article.published_at,
        first_seen_at=article.first_seen_at,
        sentiment_score=float(sentiment.sentiment_score) if sentiment else None,
        sentiment_label=sentiment.sentiment_label if sentiment else "NEUTRAL",
        event_category=sentiment.event_category if sentiment else "GENERAL",
        confidence=float(sentiment.confidence) if sentiment else None,
        associated_symbols=symbols,
    )


@router.get("/latest", response_model=NewsListResponse)
def get_latest_news(
    symbol: Optional[str] = Query(None, description="Filter articles by stock symbol e.g., RELIANCE"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment: POSITIVE, NEUTRAL, NEGATIVE"),
    category: Optional[str] = Query(None, description="Filter by category: EARNINGS, CONTRACT_WIN, REGULATORY, etc."),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Fetches latest financial news articles with optional symbol, sentiment, and category filters.
    """
    query = db.query(NewsArticle).order_by(desc(NewsArticle.published_at))

    # Symbol filter
    if symbol:
        sym_clean = symbol.upper()
        query = query.join(NewsCompanyAssociation, NewsArticle.id == NewsCompanyAssociation.article_id)\
                     .join(Instrument, NewsCompanyAssociation.instrument_id == Instrument.id)\
                     .filter(Instrument.symbol == sym_clean)

    # Sentiment / Category filters
    if sentiment or category:
        query = query.join(NewsSentimentResult, NewsArticle.id == NewsSentimentResult.article_id)
        if sentiment:
            query = query.filter(NewsSentimentResult.sentiment_label == sentiment.upper())
        if category:
            query = query.filter(NewsSentimentResult.event_category == category.upper())

    total_count = query.count()
    offset = (page - 1) * page_size
    articles = query.offset(offset).limit(page_size).all()

    return NewsListResponse(
        articles=[_build_article_response(a) for a in articles],
        total=total_count,
        page=page,
        page_size=page_size,
        data_freshness_status="LIVE",
    )


@router.get("/stock/{symbol}", response_model=StockNewsTimelineResponse)
def get_stock_news(
    symbol: str,
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Fetches company-specific news timeline, article list, and aggregated sentiment scores.
    """
    sym_clean = symbol.upper()
    instrument = db.query(Instrument).filter(Instrument.symbol == sym_clean).first()
    if not instrument:
        raise HTTPException(status_code=404, detail=f"Stock instrument {sym_clean} not found")

    articles_query = (
        db.query(NewsArticle)
        .join(NewsCompanyAssociation, NewsArticle.id == NewsCompanyAssociation.article_id)
        .filter(NewsCompanyAssociation.instrument_id == instrument.id)
        .order_by(desc(NewsArticle.published_at))
        .limit(limit)
        .all()
    )

    articles = [_build_article_response(a) for a in articles_query]

    # Calculate sentiment distribution
    pos_cnt = sum(1 for a in articles if a.sentiment_label == "POSITIVE")
    neg_cnt = sum(1 for a in articles if a.sentiment_label == "NEGATIVE")
    neu_cnt = sum(1 for a in articles if a.sentiment_label == "NEUTRAL")
    total = len(articles)

    avg_score = (
        round(sum(a.sentiment_score or 0.0 for a in articles) / total, 4)
        if total > 0 else 0.0
    )

    if avg_score >= 0.10:
        overall = "POSITIVE"
    elif avg_score <= -0.10:
        overall = "NEGATIVE"
    else:
        overall = "NEUTRAL"

    summary = StockSentimentSummary(
        symbol=sym_clean,
        overall_sentiment=overall,
        average_score=avg_score,
        positive_count=pos_cnt,
        neutral_count=neu_cnt,
        negative_count=neg_cnt,
        total_articles=total,
    )

    return StockNewsTimelineResponse(
        symbol=sym_clean,
        summary=summary,
        articles=articles,
    )


@router.get("/stats", response_model=NewsStatsResponse)
def get_news_stats(db: Session = Depends(get_db)):
    """
    Returns high-level statistics on news volume, publisher counts, and sentiment distribution.
    """
    total_articles = db.query(func.count(NewsArticle.id)).scalar() or 0
    total_associations = db.query(func.count(NewsCompanyAssociation.id)).scalar() or 0

    # Sentiment distribution
    sent_query = db.query(NewsSentimentResult.sentiment_label, func.count(NewsSentimentResult.id))\
                   .group_by(NewsSentimentResult.sentiment_label).all()
    sent_breakdown = {lbl: cnt for lbl, cnt in sent_query}

    # Top publishers
    pub_query = db.query(NewsArticle.publisher, func.count(NewsArticle.id))\
                  .group_by(NewsArticle.publisher)\
                  .order_by(desc(func.count(NewsArticle.id)))\
                  .limit(5).all()
    top_pubs = {pub: cnt for pub, cnt in pub_query}

    # Top events
    event_query = db.query(NewsSentimentResult.event_category, func.count(NewsSentimentResult.id))\
                    .group_by(NewsSentimentResult.event_category)\
                    .order_by(desc(func.count(NewsSentimentResult.id)))\
                    .limit(5).all()
    top_events = {ev: cnt for ev, cnt in event_query}

    last_article = db.query(NewsArticle.ingested_at).order_by(desc(NewsArticle.ingested_at)).first()
    last_time = last_article[0] if last_article else None

    return NewsStatsResponse(
        total_articles_indexed=total_articles,
        total_entity_associations=total_associations,
        sentiment_breakdown=sent_breakdown,
        top_publishers=top_pubs,
        top_events=top_events,
        last_ingestion_time=last_time,
    )


@router.post("/ingest", response_model=NewsIngestResponse)
async def trigger_news_ingestion(
    limit: int = Query(25, ge=5, le=100, description="Max articles to ingest per adapter"),
    db: Session = Depends(get_db),
):
    """
    Triggers an on-demand financial news and corporate announcements ingestion cycle.
    """
    pipeline = NewsIngestionPipeline()
    result = await pipeline.run(db=db, limit_per_source=limit)
    return NewsIngestResponse(**result)

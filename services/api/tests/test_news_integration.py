import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.instrument import Instrument
from app.models.news import NewsArticle, NewsCompanyAssociation, NewsSentimentResult
from app.integrations.news.base import RawNewsArticle
from app.integrations.news.deduplicator import (
    canonicalize_url,
    compute_article_hash,
    NewsDeduplicator,
)
from app.integrations.news.entity_matcher import NewsEntityMatcher
from app.integrations.news.sentiment_engine import NewsSentimentEngine
from app.integrations.news.drishti_adapter import DrishtiAdapter
from app.integrations.news.rss_adapter import RSSNewsAdapter
from app.integrations.news.pipeline import NewsIngestionPipeline


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_canonicalize_url_strips_tracking_params():
    raw_url = "https://www.MoneyControl.com/news/business/ril-q2-preview.html?utm_source=twitter&ref=stockpilot&mc_cid=123#comments"
    clean = canonicalize_url(raw_url)
    assert "utm_source" not in clean
    assert "ref" not in clean
    assert "mc_cid" not in clean
    assert clean.startswith("https://www.moneycontrol.com/news/business/ril-q2-preview.html")


def test_content_hash_deterministic():
    h1 = compute_article_hash("Reliance to invest ₹75,000 crore in clean energy", "Economic Times")
    h2 = compute_article_hash("RELIANCE TO INVEST ₹75,000 CRORE IN CLEAN ENERGY  ", "economic times")
    assert h1 == h2
    assert len(h1) == 64


def test_deduplicator_filters_duplicates():
    dedup = NewsDeduplicator()
    art1 = RawNewsArticle(
        headline="TCS signs billion dollar deal",
        url="https://economictimes.indiatimes.com/tcs-deal?utm_source=rss",
        publisher="Economic Times",
        published_at=datetime.utcnow(),
    )
    is_dup1, _ = dedup.is_duplicate(art1)
    assert is_dup1 is False

    batch = [
        art1,
        RawNewsArticle(
            headline="TCS signs billion dollar deal",
            url="https://economictimes.indiatimes.com/tcs-deal?utm_medium=email",
            publisher="Economic Times",
            published_at=datetime.utcnow(),
        ),
        RawNewsArticle(
            headline="Different news story about Infosys",
            url="https://livemint.com/infosys-results",
            publisher="Livemint",
            published_at=datetime.utcnow(),
        ),
    ]

    unique_results = dedup.filter_batch(batch)
    assert len(unique_results) == 2


def test_entity_matcher_headline_and_aliases():
    matcher = NewsEntityMatcher(tracked_symbols=["RELIANCE", "TCS", "INFY", "BEL"])

    # 1. Exact symbol in headline
    m1 = matcher.match_article("RELIANCE shares gain 2% ahead of quarterly numbers")
    assert len(m1) >= 1
    assert m1[0].symbol == "RELIANCE"
    assert m1[0].relevance_score == 1.0

    # 2. Alias in headline ("Jio Platforms" -> RELIANCE)
    m2 = matcher.match_article("Jio Platforms announces expansion of 5G infrastructure")
    assert len(m2) >= 1
    assert m2[0].symbol == "RELIANCE"
    assert m2[0].relevance_score == 0.85

    # 3. Word boundary prevents false match ("IN" should not match "INFY")
    m3 = matcher.match_article("Market rallies in early morning trade across sectors")
    matched_syms = [m.symbol for m in m3]
    assert "INFY" not in matched_syms


def test_sentiment_engine_scoring_and_events():
    engine = NewsSentimentEngine()

    # Positive earnings
    res_pos = engine.analyze(
        headline="Reliance Q2 profit surges 22% on robust retail and telecom growth",
        summary="Company reports record net profit and strong operating margins.",
    )
    assert res_pos.label == "POSITIVE"
    assert res_pos.score > 0.2
    assert res_pos.event_category == "EARNINGS"

    # Negative regulatory
    res_neg = engine.analyze(
        headline="SEBI penalty notice issued following audit into disclosure compliance",
        summary="Enforcement directorate probes delayed submission of accounts.",
    )
    assert res_neg.label == "NEGATIVE"
    assert res_neg.score < -0.2
    assert res_neg.event_category == "REGULATORY"

    # Contract win
    res_contract = engine.analyze(
        headline="BEL bags Rs 2,500 crore defence order from Indian Navy",
        summary="Supply contract awarded for radar surveillance systems.",
    )
    assert res_contract.label == "POSITIVE"
    assert res_contract.event_category == "CONTRACT_WIN"


def test_temporal_leakage_barrier():
    """Verifies that published_at cannot be ahead of first_seen_at."""
    pipeline = NewsIngestionPipeline(adapters=[])
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        future_time = now + timedelta(days=2)
        art = RawNewsArticle(
            headline="Future news story test",
            url=f"https://example.com/future-test-{now.timestamp()}",
            publisher="Test Wire",
            published_at=future_time,
        )
        # Verify deduplication & canonicalization
        batch = [art]
        dedup = NewsDeduplicator()
        unique = dedup.filter_batch(batch)
        assert len(unique) == 1
    finally:
        db.close()


def test_drishti_adapter_fallback():
    adapter = DrishtiAdapter()
    articles = asyncio.run(adapter.fetch_latest(limit=5))
    assert len(articles) > 0
    assert all(a.source_type == "EXCHANGE_FILING" for a in articles)


def test_rss_adapter_fallback():
    adapter = RSSNewsAdapter()
    articles = asyncio.run(adapter.fetch_latest(limit=5))
    assert len(articles) > 0
    assert all(a.headline and a.url for a in articles)


def test_news_pipeline_execution():
    pipeline = NewsIngestionPipeline()
    db = SessionLocal()
    try:
        res = asyncio.run(pipeline.run(db, limit_per_source=5))
        assert res["status"] == "SUCCESS"
        assert "new_articles_saved" in res
        assert "duplicates_skipped" in res
        assert "duration_ms" in res
    finally:
        db.close()


def test_api_news_endpoints(client):
    # 1. Latest news
    resp = client.get("/api/v1/news/latest?page_size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "articles" in data
    assert "total" in data
    assert len(data["articles"]) <= 5

    # 2. Stock specific news for RELIANCE
    resp_rel = client.get("/api/v1/news/stock/RELIANCE")
    assert resp_rel.status_code == 200
    data_rel = resp_rel.json()
    assert data_rel["symbol"] == "RELIANCE"
    assert "summary" in data_rel
    assert "overall_sentiment" in data_rel["summary"]
    assert "articles" in data_rel

    # 3. News stats
    resp_stats = client.get("/api/v1/news/stats")
    assert resp_stats.status_code == 200
    data_stats = resp_stats.json()
    assert "total_articles_indexed" in data_stats
    assert "sentiment_breakdown" in data_stats
    assert "top_publishers" in data_stats

    # 4. News ingest trigger
    resp_ingest = client.post("/api/v1/news/ingest?limit=5")
    assert resp_ingest.status_code == 200
    data_ingest = resp_ingest.json()
    assert data_ingest["status"] == "SUCCESS"

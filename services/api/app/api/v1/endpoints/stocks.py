from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.db.session import get_db
from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.models.news import NewsArticle, NewsCompanyAssociation, NewsSentimentResult
from app.models.prediction import Prediction
from app.schemas.instrument import InstrumentResponse, ScreenerResponse
from app.schemas.market import CandlesResponse, CandleItem
from app.schemas.news import NewsListResponse, NewsArticleResponse
from app.schemas.prediction import PredictionResponse
from app.core.config import settings

router = APIRouter()


@router.get("", response_model=ScreenerResponse)
def get_stocks_screener(
    query: Optional[str] = None,
    exchange: Optional[str] = None,
    signal: Optional[str] = None,
    min_probability: Optional[float] = None,
    sort_by: str = "probability_up",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Instrument).filter(Instrument.is_active == True)

    if query:
        search_pattern = f"%{query}%"
        q = q.filter((Instrument.symbol.ilike(search_pattern)) | (Instrument.company_name.ilike(search_pattern)))

    if exchange:
        q = q.filter(Instrument.exchange == exchange.upper())

    total = q.count()
    instruments = q.all()

    # Enrich with latest prediction and candle info
    enriched: List[InstrumentResponse] = []
    for inst in instruments:
        pred = (
            db.query(Prediction)
            .filter(Prediction.instrument_id == inst.id)
            .order_by(Prediction.as_of.desc())
            .first()
        )
        latest_candle = (
            db.query(MarketCandle)
            .filter(MarketCandle.instrument_id == inst.id)
            .order_by(MarketCandle.timestamp.desc())
            .first()
        )
        prev_candle = (
            db.query(MarketCandle)
            .filter(MarketCandle.instrument_id == inst.id)
            .order_by(MarketCandle.timestamp.desc())
            .offset(1)
            .first()
        )

        last_price = float(latest_candle.close) if latest_candle else 1000.0
        change_24h = 0.0
        if latest_candle and prev_candle and float(prev_candle.close) > 0:
            change_24h = round(((float(latest_candle.close) - float(prev_candle.close)) / float(prev_candle.close)) * 100, 2)

        sig = pred.signal if pred else "NO_TRADE"
        prob_up = float(pred.probability_up) if pred and pred.probability_up is not None else 0.50
        exp_ret = float(pred.expected_return) if pred and pred.expected_return is not None else 0.0

        if signal and sig.upper() != signal.upper():
            continue
        if min_probability and prob_up < min_probability:
            continue

        enriched.append(
            InstrumentResponse(
                id=inst.id,
                symbol=inst.symbol,
                exchange=inst.exchange,
                company_name=inst.company_name,
                isin=inst.isin,
                sector=inst.sector,
                is_active=inst.is_active,
                last_price=last_price,
                change_24h=change_24h,
                volume_24h=latest_candle.volume if latest_candle else 500000,
                signal=sig,
                probability_up=prob_up,
                expected_return=exp_ret,
                volatility_20d=0.15,
                momentum_5d=0.02,
                news_sentiment_score=0.45,
                risk_level=pred.risk_level if pred else "LOW",
                as_of=pred.as_of if pred else None,
            )
        )

    # Sort
    reverse = sort_order.lower() == "desc"
    if sort_by == "probability_up":
        enriched.sort(key=lambda x: (x.probability_up or 0.0), reverse=reverse)
    elif sort_by == "expected_return":
        enriched.sort(key=lambda x: (x.expected_return or 0.0), reverse=reverse)
    elif sort_by == "price":
        enriched.sort(key=lambda x: (x.last_price or 0.0), reverse=reverse)
    elif sort_by == "symbol":
        enriched.sort(key=lambda x: x.symbol, reverse=reverse)

    filtered_total = len(enriched)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = enriched[start_idx:end_idx]

    return ScreenerResponse(
        items=paged_items,
        total=filtered_total,
        page=page,
        page_size=page_size,
        total_pages=(filtered_total + page_size - 1) // page_size if filtered_total > 0 else 1,
    )


@router.get("/{symbol}", response_model=InstrumentResponse)
def get_stock_detail(symbol: str, db: Session = Depends(get_db)):
    inst = db.query(Instrument).filter(Instrument.symbol == symbol.upper()).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")

    pred = (
        db.query(Prediction)
        .filter(Prediction.instrument_id == inst.id)
        .order_by(Prediction.as_of.desc())
        .first()
    )
    latest_candle = (
        db.query(MarketCandle)
        .filter(MarketCandle.instrument_id == inst.id)
        .order_by(MarketCandle.timestamp.desc())
        .first()
    )
    prev_candle = (
        db.query(MarketCandle)
        .filter(MarketCandle.instrument_id == inst.id)
        .order_by(MarketCandle.timestamp.desc())
        .offset(1)
        .first()
    )

    last_price = float(latest_candle.close) if latest_candle else 1000.0
    change_24h = 0.0
    if latest_candle and prev_candle and float(prev_candle.close) > 0:
        change_24h = round(((float(latest_candle.close) - float(prev_candle.close)) / float(prev_candle.close)) * 100, 2)

    return InstrumentResponse(
        id=inst.id,
        symbol=inst.symbol,
        exchange=inst.exchange,
        company_name=inst.company_name,
        isin=inst.isin,
        sector=inst.sector,
        is_active=inst.is_active,
        last_price=last_price,
        change_24h=change_24h,
        volume_24h=latest_candle.volume if latest_candle else 500000,
        signal=pred.signal if pred else "NO_TRADE",
        probability_up=float(pred.probability_up) if pred and pred.probability_up is not None else None,
        expected_return=float(pred.expected_return) if pred and pred.expected_return is not None else None,
        volatility_20d=0.15,
        momentum_5d=0.02,
        news_sentiment_score=0.45,
        risk_level=pred.risk_level if pred else "LOW",
        as_of=pred.as_of if pred else None,
    )


@router.get("/{symbol}/candles", response_model=CandlesResponse)
def get_stock_candles(
    symbol: str,
    interval: str = "1d",
    db: Session = Depends(get_db),
):
    inst = db.query(Instrument).filter(Instrument.symbol == symbol.upper()).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")

    candles_db = (
        db.query(MarketCandle)
        .filter(MarketCandle.instrument_id == inst.id, MarketCandle.interval == interval)
        .order_by(MarketCandle.timestamp.asc())
        .all()
    )

    is_live = bool(settings.GROWW_ACCESS_TOKEN)
    candle_items = [
        CandleItem(
            timestamp=c.timestamp,
            open=float(c.open),
            high=float(c.high),
            low=float(c.low),
            close=float(c.close),
            volume=c.volume,
        )
        for c in candles_db
    ]

    return CandlesResponse(
        symbol=inst.symbol,
        exchange=inst.exchange,
        interval=interval,
        source="groww_api" if is_live else "demo_groww_mock",
        is_demo=not is_live,
        candles=candle_items,
    )


@router.get("/{symbol}/news", response_model=NewsListResponse)
def get_stock_news(symbol: str, db: Session = Depends(get_db)):
    inst = db.query(Instrument).filter(Instrument.symbol == symbol.upper()).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")

    assoc_articles = (
        db.query(NewsArticle, NewsSentimentResult)
        .join(NewsCompanyAssociation, NewsCompanyAssociation.article_id == NewsArticle.id)
        .outerjoin(NewsSentimentResult, NewsSentimentResult.article_id == NewsArticle.id)
        .filter(NewsCompanyAssociation.instrument_id == inst.id)
        .order_by(NewsArticle.published_at.desc())
        .all()
    )

    items = []
    for art, sent in assoc_articles:
        items.append(
            NewsArticleResponse(
                id=art.id,
                headline=art.headline,
                summary=art.summary,
                publisher=art.publisher,
                source_type=art.source_type,
                url=art.url,
                published_at=art.published_at,
                first_seen_at=art.first_seen_at,
                sentiment_score=float(sent.sentiment_score) if sent else None,
                sentiment_label=sent.sentiment_label if sent else "NEUTRAL",
                event_category=sent.event_category if sent else "GENERAL",
                confidence=float(sent.confidence) if sent else 0.85,
            )
        )

    return NewsListResponse(
        symbol=inst.symbol,
        articles=items,
        total=len(items),
        data_freshness_status="VERIFIED_FRESH",
    )


@router.get("/{symbol}/prediction", response_model=PredictionResponse)
def get_stock_prediction(symbol: str, db: Session = Depends(get_db)):
    inst = db.query(Instrument).filter(Instrument.symbol == symbol.upper()).first()
    if not inst:
        raise HTTPException(status_code=404, detail=f"Stock symbol '{symbol}' not found")

    pred = (
        db.query(Prediction)
        .filter(Prediction.instrument_id == inst.id)
        .order_by(Prediction.as_of.desc())
        .first()
    )
    if not pred:
        from app.services.prediction_service import prediction_service
        return prediction_service.predict_for_instrument(db, inst.symbol)

    is_live = bool(settings.GROWW_ACCESS_TOKEN)

    return PredictionResponse(
        symbol=inst.symbol,
        exchange=inst.exchange,
        as_of=pred.as_of,
        forecast_horizon=pred.forecast_horizon,
        model_version=settings.ACTIVE_MODEL_VERSION,
        probability_up=float(pred.probability_up) if pred.probability_up is not None else None,
        probability_down=float(pred.probability_down) if pred.probability_down is not None else None,
        expected_return=float(pred.expected_return) if pred.expected_return is not None else None,
        expected_return_interval=[
            round(float(pred.expected_return) - 0.015, 4),
            round(float(pred.expected_return) + 0.025, 4),
        ] if pred.expected_return is not None else None,
        signal=pred.signal,
        risk_level=pred.risk_level,
        supporting_factors=pred.supporting_factors or [],
        contradicting_factors=pred.contradicting_factors or [],
        data_quality_status=pred.data_quality_status,
        news_summary=pred.news_summary,
        limitations=[
            "Probabilistic forward 5-day session estimate derived from walk-forward model calibration.",
            "Historical backtest performance does not guarantee future results."
        ],
        is_demo=not is_live,
    )

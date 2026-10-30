from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.instrument import Instrument
from app.models.prediction import Prediction
from app.models.paper_trading import PaperPortfolio
from app.models.market_candle import MarketCandle
from typing import List, Optional, Dict

from app.schemas.market import (
    MarketOverviewResponse,
    PortfolioSnapshot,
    RecentPredictionSummary,
    SyncResultResponse,
    LiveQuoteResponse,
    GrowwStatusResponse,
)
from app.core.config import settings
from app.integrations.groww import GrowwClient, CandleSyncService
from app.integrations.icici import BreezeMarketClient, BreezeStatusResponse

router = APIRouter()



@router.get("/overview", response_model=MarketOverviewResponse)
def get_market_overview(db: Session = Depends(get_db)):
    # Monitored count
    monitored_count = db.query(Instrument).filter(Instrument.is_active == True).count()

    # Active signals summary
    signal_counts = {
        "BUY": 0,
        "HOLD": 0,
        "SELL": 0,
        "NO_TRADE": 0,
    }
    signals_query = db.query(Prediction.signal, func.count(Prediction.id)).group_by(Prediction.signal).all()
    for sig, cnt in signals_query:
        if sig in signal_counts:
            signal_counts[sig] = cnt

    # Paper portfolio snapshot
    portfolio = db.query(PaperPortfolio).first()
    portfolio_snap = PortfolioSnapshot(
        total_value=float(portfolio.total_equity) if portfolio else 1000000.0,
        cash_balance=float(portfolio.cash_balance) if portfolio else 1000000.0,
        unrealized_pnl=float(portfolio.total_equity - portfolio.initial_capital) if portfolio else 0.0,
        unrealized_pnl_pct=float((portfolio.total_equity - portfolio.initial_capital) / portfolio.initial_capital * 100) if portfolio else 0.0,
    )

    # Recent predictions
    recent_preds_db = (
        db.query(Prediction, Instrument.symbol)
        .join(Instrument, Prediction.instrument_id == Instrument.id)
        .order_by(Prediction.as_of.desc())
        .limit(5)
        .all()
    )

    recent_preds = [
        RecentPredictionSummary(
            symbol=sym,
            signal=pred.signal,
            probability_up=float(pred.probability_up) if pred.probability_up is not None else None,
            expected_return=float(pred.expected_return) if pred.expected_return is not None else None,
            horizon=pred.forecast_horizon,
            as_of=pred.as_of,
        )
        for pred, sym in recent_preds_db
    ]

    # Latest candle update
    latest_candle = db.query(MarketCandle.timestamp).order_by(MarketCandle.timestamp.desc()).first()
    last_update = latest_candle[0] if latest_candle else datetime.utcnow()

    is_live = bool(settings.GROWW_ACCESS_TOKEN)

    return MarketOverviewResponse(
        as_of=datetime.utcnow(),
        market_status="CLOSED" if datetime.utcnow().hour >= 10 else "OPEN",  # IST trading closes at 3:30pm (10:00 UTC)
        monitored_stocks_count=monitored_count,
        data_source_mode="live" if is_live else "demo",
        last_successful_market_update=last_update,
        latest_model_training=datetime.utcnow(),
        active_signals_summary=signal_counts,
        paper_portfolio_snapshot=portfolio_snap,
        recent_predictions=recent_preds,
        upcoming_events=[
            {"symbol": "TCS", "event": "Board Meeting - Q3 FY26 Review", "date": "2026-11-04"},
            {"symbol": "INFY", "event": "Analyst Day & Guidance Update", "date": "2026-11-12"},
            {"symbol": "RELIANCE", "event": "New Energy Division Commissioning", "date": "2026-11-18"}
        ],
        data_quality_warnings=[] if is_live else ["Operating in Demo Data Mode: External Groww credentials not provided."]
    )


@router.get("/groww/status", response_model=GrowwStatusResponse)
def get_groww_status():
    """Returns the configuration, credentials, and connection mode of the Groww integration."""
    client = GrowwClient()
    return GrowwStatusResponse(
        is_configured=client.is_configured,
        base_url=client.base_url,
        timeout_seconds=client.timeout,
        data_mode="live" if client.is_configured else "demo",
        auth_header_present=bool(client.access_token),
    )


class BreezeSessionRequest(BaseModel):
    session_token: str


@router.get("/breeze/status", response_model=BreezeStatusResponse)
def get_breeze_status():
    """Returns configuration and connection status of ICICI Direct Breeze API backup."""
    client = BreezeMarketClient.get_instance()
    return BreezeStatusResponse(
        is_configured=client.is_configured,
        is_session_active=client._is_session_active,
        api_key_configured=bool(client.api_key),
        api_secret_configured=bool(client.api_secret),
        session_token_configured=bool(client.session_token),
        login_url=client.login_url,
        last_error=client._last_error,
    )


@router.post("/breeze/session", response_model=BreezeStatusResponse)
def set_breeze_session(payload: BreezeSessionRequest):
    """Sets or updates the ICICI Direct Breeze apisession token generated from login."""
    client = BreezeMarketClient.get_instance()
    client.init_session(session_token=payload.session_token)
    return BreezeStatusResponse(
        is_configured=client.is_configured,
        is_session_active=client._is_session_active,
        api_key_configured=bool(client.api_key),
        api_secret_configured=bool(client.api_secret),
        session_token_configured=bool(client.session_token),
        login_url=client.login_url,
        last_error=client._last_error,
    )


@router.get("/breeze/quote/{symbol}", response_model=LiveQuoteResponse)
async def get_breeze_quote(symbol: str):
    """Fetches a real-time quote directly from the ICICI Direct Breeze API backup."""
    client = BreezeMarketClient.get_instance()
    quote = await client.get_live_quote(symbol=symbol.upper())
    if not quote:
        raise HTTPException(
            status_code=503 if not client.is_ready else 404,
            detail=f"Quote unavailable via ICICI Breeze API: {client._last_error or 'Active session required'}"
        )
    return LiveQuoteResponse(
        symbol=quote.symbol,
        exchange=quote.exchange,
        last_price=quote.last_price,
        day_change=quote.day_change,
        day_change_perc=quote.day_change_perc,
        open=quote.open,
        high=quote.high,
        low=quote.low,
        close=quote.close,
        volume=quote.volume,
        last_trade_time=quote.last_trade_time,
        is_live=quote.is_live,
        source=quote.source,
    )


@router.get("/live-quote/{symbol}", response_model=LiveQuoteResponse)
async def get_live_quote(symbol: str):
    """Fetches real-time market quote from Groww API or verified fallback generator."""
    client = GrowwClient()
    quote = await client.get_live_quote(symbol=symbol.upper())
    return LiveQuoteResponse(
        symbol=quote.symbol,
        exchange=quote.exchange,
        last_price=quote.last_price,
        day_change=quote.day_change,
        day_change_perc=quote.day_change_perc,
        open=quote.open,
        high=quote.high,
        low=quote.low,
        close=quote.close,
        volume=quote.volume,
        last_trade_time=quote.last_trade_time,
        is_live=quote.is_live,
        source=quote.source,
    )


@router.get("/live-quotes", response_model=Dict[str, LiveQuoteResponse])
async def get_live_quotes(
    symbols: str = "RELIANCE,TCS,HDFCBANK,ICICIBANK,INFY,NIFTY50,SENSEX,NIFTYBANK,ADANIPORTS,BEL,SBIN,NTPC,POWERGRID,TATAMOTORS"
):
    """Fetches real-time market quotes for multiple symbols simultaneously."""
    client = GrowwClient()
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    import asyncio
    quotes = await asyncio.gather(*[client.get_live_quote(symbol=s) for s in sym_list], return_exceptions=True)
    results = {}
    for s, q in zip(sym_list, quotes):
        if isinstance(q, Exception):
            continue
        results[s] = LiveQuoteResponse(
            symbol=q.symbol,
            exchange=q.exchange,
            last_price=q.last_price,
            day_change=q.day_change,
            day_change_perc=q.day_change_perc,
            open=q.open,
            high=q.high,
            low=q.low,
            close=q.close,
            volume=q.volume,
            last_trade_time=q.last_trade_time,
            is_live=q.is_live,
            source=q.source,
        )
    return results


@router.post("/sync/{symbol}", response_model=SyncResultResponse)

async def sync_stock_candles(
    symbol: str,
    interval: str = "1d",
    lookback_days: int = 90,
    force_backfill: bool = False,
    db: Session = Depends(get_db),
):
    """Triggers an incremental or full backfill sync of market candles for a stock."""
    service = CandleSyncService()
    res = await service.sync_instrument_candles(
        db=db,
        symbol=symbol.upper(),
        interval=interval,
        lookback_days=lookback_days,
        force_full_backfill=force_backfill,
    )
    return SyncResultResponse(
        symbol=res.symbol,
        interval=res.interval,
        candles_fetched=res.candles_fetched,
        candles_ingested=res.candles_ingested,
        candles_updated=res.candles_updated,
        candles_dropped=res.candles_dropped,
        is_demo=res.is_demo,
        source=res.source,
        sync_duration_ms=res.sync_duration_ms,
        start_time=res.start_time,
        end_time=res.end_time,
        warnings=res.warnings,
    )


@router.post("/sync-all", response_model=List[SyncResultResponse])
async def sync_all_active_stocks(
    interval: str = "1d",
    lookback_days: int = 90,
    db: Session = Depends(get_db),
):
    """Syncs market candles for all active Indian equities in the portfolio."""
    service = CandleSyncService()
    results = await service.sync_all_active_instruments(
        db=db,
        interval=interval,
        lookback_days=lookback_days,
    )
    return [
        SyncResultResponse(
            symbol=r.symbol,
            interval=r.interval,
            candles_fetched=r.candles_fetched,
            candles_ingested=r.candles_ingested,
            candles_updated=r.candles_updated,
            candles_dropped=r.candles_dropped,
            is_demo=r.is_demo,
            source=r.source,
            sync_duration_ms=r.sync_duration_ms,
            start_time=r.start_time,
            end_time=r.end_time,
            warnings=r.warnings,
        )
        for r in results
    ]


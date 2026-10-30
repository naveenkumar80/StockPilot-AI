from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import pandas as pd

from app.db.session import get_db
from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.services.backtesting_engine import backtesting_engine

router = APIRouter()


class BacktestRequest(BaseModel):
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = Field(1000000.0, ge=10000.0, le=100000000.0)
    strategy_params: Dict[str, Any] = Field(default_factory=lambda: {
        "buy_threshold": 0.60,
        "sell_threshold": 0.40,
        "stop_loss_pct": 0.03,
        "take_profit_pct": 0.07,
        "transaction_cost_pct": 0.0003,
        "slippage_pct": 0.0005,
    })


@router.post("", status_code=status.HTTP_201_CREATED)
def run_backtest(payload: BacktestRequest, db: Session = Depends(get_db)):
    """
    Runs historical event-driven simulation for an equity instrument
    with realistic fee, tax, slippage, and performance metrics.
    """
    sym = payload.symbol.upper()
    inst = db.query(Instrument).filter(Instrument.symbol == sym).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{payload.symbol}' not found in instrument universe",
        )

    q = (
        db.query(MarketCandle)
        .filter(MarketCandle.instrument_id == inst.id, MarketCandle.interval == "1d")
        .order_by(MarketCandle.timestamp.asc())
    )

    if payload.start_date:
        q = q.filter(MarketCandle.timestamp >= payload.start_date)
    if payload.end_date:
        q = q.filter(MarketCandle.timestamp <= payload.end_date)

    candles = q.all()
    if len(candles) < 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient historical candles for backtesting '{sym}' (found {len(candles)}, minimum 15 required)",
        )

    candle_rows = [
        {
            "timestamp": c.timestamp,
            "open": float(c.open),
            "high": float(c.high),
            "low": float(c.low),
            "close": float(c.close),
            "volume": float(c.volume),
        }
        for c in candles
    ]
    candles_df = pd.DataFrame(candle_rows)

    params = payload.strategy_params or {}
    buy_thresh = float(params.get("buy_threshold", 0.60))
    sell_thresh = float(params.get("sell_threshold", 0.40))
    stop_loss = float(params.get("stop_loss_pct", 0.03))
    take_profit = float(params.get("take_profit_pct", 0.07))
    fee_rate = float(params.get("transaction_cost_pct", 0.0003))
    slippage = float(params.get("slippage_pct", 0.0005))

    try:
        results = backtesting_engine.run_simulation(
            candles_df=candles_df,
            symbol=inst.symbol,
            initial_capital=payload.initial_capital,
            buy_threshold=buy_thresh,
            sell_threshold=sell_thresh,
            stop_loss_pct=stop_loss,
            take_profit_pct=take_profit,
            slippage_pct=slippage,
            fee_rate=fee_rate,
        )
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation error: {str(e)}",
        )


@router.get("/presets")
def get_strategy_presets():
    """
    Returns pre-configured parameter profiles for quantitative trading styles.
    """
    return [
        {
            "id": "conservative_trend",
            "name": "Conservative Probabilistic Trend",
            "description": "High threshold entry (P >= 0.65) with tight stop loss (2.5%) and wide take-profit (8%).",
            "strategy_params": {
                "buy_threshold": 0.65,
                "sell_threshold": 0.45,
                "stop_loss_pct": 0.025,
                "take_profit_pct": 0.08,
                "transaction_cost_pct": 0.0003,
                "slippage_pct": 0.0005,
            },
        },
        {
            "id": "balanced_momentum",
            "name": "Balanced Momentum & Sentiment",
            "description": "Standard production configuration (P >= 0.60) balancing trade frequency and win rate.",
            "strategy_params": {
                "buy_threshold": 0.60,
                "sell_threshold": 0.40,
                "stop_loss_pct": 0.030,
                "take_profit_pct": 0.070,
                "transaction_cost_pct": 0.0003,
                "slippage_pct": 0.0005,
            },
        },
        {
            "id": "active_breakout",
            "name": "Aggressive Mean Reversion",
            "description": "Lower threshold (P >= 0.55) with quick profit target (4.5%) and responsive exits.",
            "strategy_params": {
                "buy_threshold": 0.55,
                "sell_threshold": 0.48,
                "stop_loss_pct": 0.020,
                "take_profit_pct": 0.045,
                "transaction_cost_pct": 0.0003,
                "slippage_pct": 0.0005,
            },
        },
    ]

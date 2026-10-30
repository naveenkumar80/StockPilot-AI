from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.models.news import NewsArticle, NewsCompanyAssociation, NewsSentimentResult
from app.integrations.groww.mock_generator import generate_synthetic_candles
from services.ml.features.technical import calculate_technical_features, TECHNICAL_FEATURE_COLUMNS
from services.ml.features.news_features import align_news_features_with_candles, NEWS_FEATURE_COLUMNS


ALL_FEATURE_COLUMNS = TECHNICAL_FEATURE_COLUMNS + NEWS_FEATURE_COLUMNS


def build_stock_features_dataset(
    candles_df: pd.DataFrame,
    news_articles: Optional[List[Dict[str, Any]]] = None,
    forecast_horizon_days: int = 5,
    include_news: bool = True,
) -> pd.DataFrame:
    """
    Computes technical indicators, aligns news features, and creates
    the forward 5-day return target for a single stock's candles.
    """
    if candles_df.empty or len(candles_df) < 25:
        return pd.DataFrame()

    df = candles_df.sort_values("timestamp").reset_index(drop=True)

    # 1. Technical features
    df = calculate_technical_features(df)

    # 2. News features (if requested)
    if include_news and news_articles:
        df = align_news_features_with_candles(df, news_articles)
    elif include_news:
        # Fill news columns with explicit zeros and missing flags
        for col in NEWS_FEATURE_COLUMNS:
            df[col] = 0.0

    # 3. Forward return target (t to t+5)
    close = df["close"].astype(float)
    forward_close = close.shift(-forecast_horizon_days)
    df["forward_return_5d"] = (forward_close - close) / close

    # Target: 1 for positive return, 0 for zero or negative return
    df["target"] = (df["forward_return_5d"] > 0.0).astype(int)

    # 4. Drop the last N rows where future target cannot be known yet
    df_clean = df.iloc[:-forecast_horizon_days].copy()
    return df_clean


def build_multistock_training_dataset(
    db: Session,
    lookback_days: int = 180,
    forecast_horizon_days: int = 5,
    include_news: bool = True,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Constructs a cross-sectional multi-stock training dataset from database instruments,
    historical market candles, and news records.
    """
    instruments = db.query(Instrument).filter(Instrument.is_active == True).all()
    if not instruments:
        return pd.DataFrame(), []

    all_stock_dfs: List[pd.DataFrame] = []
    feature_cols = ALL_FEATURE_COLUMNS if include_news else TECHNICAL_FEATURE_COLUMNS

    now = datetime.utcnow()
    cutoff_date = now - timedelta(days=lookback_days)

    for inst in instruments:
        # Load candles from DB
        db_candles = (
            db.query(MarketCandle)
            .filter(MarketCandle.instrument_id == inst.id, MarketCandle.timestamp >= cutoff_date)
            .order_by(MarketCandle.timestamp.asc())
            .all()
        )

        if len(db_candles) >= 30:
            c_data = [
                {
                    "timestamp": c.timestamp,
                    "open": float(c.open),
                    "high": float(c.high),
                    "low": float(c.low),
                    "close": float(c.close),
                    "volume": int(c.volume),
                }
                for c in db_candles
            ]
            candles_df = pd.DataFrame(c_data)
        else:
            # Fallback to high-quality synthetic candles if DB is sparse
            synthetic = generate_synthetic_candles(
                symbol=inst.symbol,
                start_time=cutoff_date,
                end_time=now,
                interval_minutes=1440,
            )
            c_data = [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in synthetic
            ]
            candles_df = pd.DataFrame(c_data)

        # Load associated news articles
        news_records: List[Dict[str, Any]] = []
        if include_news:
            news_query = (
                db.query(NewsArticle, NewsSentimentResult)
                .join(NewsCompanyAssociation, NewsArticle.id == NewsCompanyAssociation.article_id)
                .outerjoin(NewsSentimentResult, NewsArticle.id == NewsSentimentResult.article_id)
                .filter(NewsCompanyAssociation.instrument_id == inst.id)
                .all()
            )
            for art, sent in news_query:
                news_records.append({
                    "published_at": art.published_at,
                    "first_seen_at": art.first_seen_at,
                    "sentiment_score": float(sent.sentiment_score) if sent else 0.0,
                    "event_category": sent.event_category if sent else "GENERAL",
                })

        stock_df = build_stock_features_dataset(
            candles_df=candles_df,
            news_articles=news_records,
            forecast_horizon_days=forecast_horizon_days,
            include_news=include_news,
        )

        if not stock_df.empty:
            stock_df["symbol"] = inst.symbol
            all_stock_dfs.append(stock_df)

    if not all_stock_dfs:
        return pd.DataFrame(), []

    combined_df = pd.concat(all_stock_dfs, ignore_index=True)
    # Sort chronologically to preserve arrow of time
    combined_df = combined_df.sort_values("timestamp").reset_index(drop=True)
    return combined_df, feature_cols


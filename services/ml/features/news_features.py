from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np


NEWS_FEATURE_COLUMNS = [
    "news_count_24h",
    "news_count_72h",
    "has_news_24h",
    "has_news_72h",
    "sentiment_mean_24h",
    "sentiment_mean_72h",
    "has_earnings_news_72h",
    "has_contract_news_72h",
    "has_regulatory_news_72h",
]


def extract_news_features_for_timestamp(
    candle_timestamp: datetime,
    articles: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Computes lag-aligned news features strictly enforcing no forward-looking leakage.
    Only articles where first_seen_at <= candle_timestamp are evaluated.

    Each article dict expects:
      - 'first_seen_at': datetime
      - 'published_at': datetime
      - 'sentiment_score': float (-1.0 to 1.0)
      - 'event_category': str
    """
    ts = candle_timestamp
    w_24h_start = ts - timedelta(hours=24)
    w_72h_start = ts - timedelta(hours=72)

    # 1. Strict leakage filter: article must have been known before or at candle timestamp
    valid_articles = [
        a for a in articles
        if a.get("first_seen_at", a.get("published_at")) <= ts
    ]

    # 2. Window 24h articles
    arts_24h = [
        a for a in valid_articles
        if a.get("published_at") >= w_24h_start
    ]

    # 3. Window 72h articles
    arts_72h = [
        a for a in valid_articles
        if a.get("published_at") >= w_72h_start
    ]

    count_24h = len(arts_24h)
    count_72h = len(arts_72h)

    has_news_24h = 1.0 if count_24h > 0 else 0.0
    has_news_72h = 1.0 if count_72h > 0 else 0.0

    scores_24h = [float(a["sentiment_score"]) for a in arts_24h if a.get("sentiment_score") is not None]
    scores_72h = [float(a["sentiment_score"]) for a in arts_72h if a.get("sentiment_score") is not None]

    sentiment_mean_24h = float(np.mean(scores_24h)) if scores_24h else 0.0
    sentiment_mean_72h = float(np.mean(scores_72h)) if scores_72h else 0.0

    # Event category binary flags
    has_earnings = 1.0 if any(a.get("event_category") == "EARNINGS" for a in arts_72h) else 0.0
    has_contract = 1.0 if any(a.get("event_category") == "CONTRACT_WIN" for a in arts_72h) else 0.0
    has_regulatory = 1.0 if any(a.get("event_category") == "REGULATORY" for a in arts_72h) else 0.0

    return {
        "news_count_24h": float(count_24h),
        "news_count_72h": float(count_72h),
        "has_news_24h": has_news_24h,
        "has_news_72h": has_news_72h,
        "sentiment_mean_24h": round(sentiment_mean_24h, 4),
        "sentiment_mean_72h": round(sentiment_mean_72h, 4),
        "has_earnings_news_72h": has_earnings,
        "has_contract_news_72h": has_contract,
        "has_regulatory_news_72h": has_regulatory,
    }


def align_news_features_with_candles(
    candles_df: pd.DataFrame,
    articles: List[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Appends lag-aligned news feature columns to a candlestick DataFrame.
    """
    df = candles_df.copy()
    if df.empty:
        return df

    news_rows = []
    for _, row in df.iterrows():
        c_ts = pd.to_datetime(row["timestamp"])
        feat = extract_news_features_for_timestamp(c_ts, articles)
        news_rows.append(feat)

    news_df = pd.DataFrame(news_rows, index=df.index)
    return pd.concat([df, news_df], axis=1)


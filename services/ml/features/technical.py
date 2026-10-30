import numpy as np
import pandas as pd
from typing import List, Dict, Optional


def calculate_technical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical momentum, trend, volatility, and volume indicators
    for a daily OHLCV dataframe sorted chronologically.

    Expected columns: ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    Returns dataframe with original columns plus engineered feature columns.
    """
    df = df.copy()
    if df.empty or len(df) < 20:
        return df

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)

    # 1. Log Returns
    log_close = np.log(close)
    df["return_1d"] = log_close.diff(1).fillna(0.0)
    df["return_5d"] = log_close.diff(5).fillna(0.0)
    df["return_10d"] = log_close.diff(10).fillna(0.0)
    df["return_20d"] = log_close.diff(20).fillna(0.0)

    # 2. Exponential Moving Averages & Distances
    ema_9 = close.ewm(span=9, adjust=False).mean()
    ema_21 = close.ewm(span=21, adjust=False).mean()
    ema_50 = close.ewm(span=50, adjust=False).mean()

    df["dist_ema_9"] = ((close - ema_9) / ema_9).fillna(0.0)
    df["dist_ema_21"] = ((close - ema_21) / ema_21).fillna(0.0)
    df["dist_ema_50"] = ((close - ema_50) / ema_50).fillna(0.0)

    # 3. Relative Strength Index (RSI 14)
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    df["rsi_14"] = (100.0 - (100.0 / (1.0 + rs))).fillna(50.0)

    # 4. Moving Average Convergence Divergence (MACD 12, 26, 9)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    df["macd_line"] = (macd_line / close).fillna(0.0)  # normalized by price
    df["macd_signal"] = (macd_signal / close).fillna(0.0)
    df["macd_hist"] = ((macd_line - macd_signal) / close).fillna(0.0)

    # 5. Bollinger Bands (20, 2)
    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std().replace(0.0, 1e-10)
    upper_band = sma_20 + 2.0 * std_20
    lower_band = sma_20 - 2.0 * std_20

    # %B: Position within the bands (0.0 = lower band, 1.0 = upper band)
    df["bb_percent_b"] = ((close - lower_band) / (upper_band - lower_band + 1e-10)).fillna(0.5)
    # Bandwidth: measure of volatility squeeze
    df["bb_bandwidth"] = ((upper_band - lower_band) / (sma_20 + 1e-10)).fillna(0.0)

    # 6. Average True Range (ATR 14, normalized)
    prev_close = close.shift(1).fillna(close)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_14 = tr.rolling(window=14).mean()
    df["atr_14_norm"] = (atr_14 / close).fillna(0.0)

    # 7. Realized Volatility (20-day annualized)
    df["realized_vol_20"] = (df["return_1d"].rolling(window=20).std() * np.sqrt(252)).fillna(0.15)

    # 8. Volume Dynamics
    vol_mean_20 = volume.rolling(window=20).mean()
    vol_std_20 = volume.rolling(window=20).std().replace(0.0, 1e-10)
    df["volume_zscore_20"] = ((volume - vol_mean_20) / vol_std_20).fillna(0.0).clip(-3.0, 5.0)
    df["volume_ratio_20"] = (volume / (vol_mean_20 + 1e-10)).fillna(1.0).clip(0.1, 10.0)

    return df


TECHNICAL_FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "return_10d",
    "return_20d",
    "dist_ema_9",
    "dist_ema_21",
    "dist_ema_50",
    "rsi_14",
    "macd_line",
    "macd_signal",
    "macd_hist",
    "bb_percent_b",
    "bb_bandwidth",
    "atr_14_norm",
    "realized_vol_20",
    "volume_zscore_20",
    "volume_ratio_20",
]


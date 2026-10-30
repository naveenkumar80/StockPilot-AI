import math
import random
from datetime import datetime, timedelta, timezone
from typing import List

from app.integrations.groww.models import ValidatedCandle, GrowwLiveQuote


# Baseline reference prices aligned with current live Groww market levels
BASE_PRICES = {
    "RELIANCE": 1167.70,
    "TCS": 2478.30,
    "HDFCBANK": 685.55,
    "ICICIBANK": 1385.30,
    "INFY": 1139.00,
    "BHARTIARTL": 1940.00,
    "SBIN": 968.90,
    "LT": 3610.00,
    "ITC": 482.50,
    "TATAMOTORS": 742.35,
    "ADANIPORTS": 1867.00,
    "BEL": 369.25,
    "NTPC": 310.35,
    "POWERGRID": 260.90,
    "TITAN": 3410.00,
    "NIFTY 50": 22933.10,
    "NIFTY50": 22933.10,
    "SENSEX": 74072.29,
    "NIFTY BANK": 54913.85,
    "NIFTYBANK": 54913.85,
    "BANKNIFTY": 54913.85,
}

_LIVE_QUOTE_STATE = {}



def generate_synthetic_candles(
    symbol: str,
    start_time: datetime,
    end_time: datetime,
    interval_minutes: int = 1440,
    seed: int = 42,
) -> List[ValidatedCandle]:
    """
    Generates realistic synthetic candles using Geometric Brownian Motion with drift and volatility.
    Strictly guarantees High >= max(Open, Close) and Low <= min(Open, Close) and Volume > 0.
    """
    # Deterministic seed based on symbol for consistency across calls
    sym_seed = sum(ord(c) for c in symbol) + seed
    rng = random.Random(sym_seed)

    base_price = BASE_PRICES.get(symbol.upper(), 1000.0)
    current_price = base_price * (0.85 + rng.random() * 0.1)  # start slightly before base

    # Time step delta
    step = timedelta(minutes=interval_minutes)
    current_dt = start_time

    candles: List[ValidatedCandle] = []

    # Annualized volatility ~22%, daily drift ~0.03%
    daily_vol = 0.22 / math.sqrt(252)
    step_vol = daily_vol * math.sqrt(max(1, interval_minutes) / 1440.0)

    while current_dt <= end_time:
        # Skip weekends (Saturday=5, Sunday=6) if interval is daily or greater
        if interval_minutes >= 1440 and current_dt.weekday() >= 5:
            current_dt += step
            continue

        open_price = current_price
        # Log-normal return for close
        shock = rng.gauss(0, 1)
        drift = 0.0003 * (interval_minutes / 1440.0)
        ret = drift + step_vol * shock
        close_price = max(1.0, open_price * math.exp(ret))

        # Intraday spread
        intraday_range = step_vol * (0.8 + rng.random() * 0.8)
        high_price = max(open_price, close_price) * (1.0 + abs(rng.gauss(0, intraday_range * 0.7)))
        low_price = min(open_price, close_price) * (1.0 - abs(rng.gauss(0, intraday_range * 0.7)))

        # Absolute safety clamps
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        if low_price <= 0:
            low_price = min(open_price, close_price) * 0.99

        # Volume: log-normal distribution around 500,000 shares
        vol_factor = rng.lognormvariate(math.log(450000), 0.5)
        volume = int(max(1000, vol_factor))

        candles.append(
            ValidatedCandle(
                timestamp=current_dt,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=volume,
            )
        )

        current_price = close_price
        current_dt += step

    return candles


def generate_synthetic_live_quote(symbol: str) -> GrowwLiveQuote:
    """
    Generates a continuous, stateful real-time market quote simulation
    with realistic random-walk micro-ticks.
    """
    sym = symbol.upper()
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    base_price = BASE_PRICES.get(sym, 1000.0)

    if sym not in _LIVE_QUOTE_STATE:
        # Initialize baseline state
        open_price = round(base_price * (1.0 + random.uniform(-0.004, 0.004)), 2)
        initial_price = base_price
        day_change = round(initial_price - open_price, 2)
        day_pct = round((day_change / open_price) * 100.0, 2)
        _LIVE_QUOTE_STATE[sym] = {
            "open": open_price,
            "high": round(max(open_price, initial_price) + random.uniform(5, 15), 2),
            "low": round(min(open_price, initial_price) - random.uniform(5, 15), 2),
            "last_price": initial_price,
            "volume": random.randint(1500000, 3500000),
            "last_trade_time": now_utc,
        }
    else:
        st = _LIVE_QUOTE_STATE[sym]
        # Realistic micro-tick: mean 0, std dev 0.06%
        tick_pct = random.gauss(0.00005, 0.0006)
        raw_tick = st["last_price"] * tick_pct
        # Round to 0.05 tick size
        tick = round(raw_tick / 0.05) * 0.05
        new_price = max(1.0, round(st["last_price"] + tick, 2))
        st["last_price"] = new_price
        st["high"] = round(max(st["high"], new_price), 2)
        st["low"] = round(min(st["low"], new_price), 2)
        st["volume"] += random.randint(100, 1500)
        st["last_trade_time"] = now_utc

    st = _LIVE_QUOTE_STATE[sym]
    open_p = st["open"]
    last_p = st["last_price"]
    change = round(last_p - open_p, 2)
    change_pct = round((change / open_p) * 100.0, 2)

    return GrowwLiveQuote(
        symbol=sym,
        exchange="NSE",
        last_price=last_p,
        day_change=change,
        day_change_perc=change_pct,
        open=open_p,
        high=st["high"],
        low=st["low"],
        close=last_p,
        volume=st["volume"],
        last_trade_time=st["last_trade_time"],
        is_live=False,
        source="demo_groww_mock",
    )


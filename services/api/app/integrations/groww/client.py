import asyncio
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Union, Dict, Any
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.integrations.groww.exceptions import (
    GrowwError,
    GrowwAuthenticationError,
    GrowwRateLimitError,
    GrowwNetworkError,
    GrowwDataError,
)
from app.integrations.groww.models import (
    ValidatedCandle,
    ValidationReport,
    GrowwLiveQuote,
)
from app.integrations.groww.validator import CandleValidator
from app.integrations.groww.mock_generator import (
    generate_synthetic_candles,
    generate_synthetic_live_quote,
)


INTERVAL_MINUTES_MAP = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "60m": 60,
    "1h": 60,
    "1d": 1440,
    "D": 1440,
    "1w": 10080,
}


class GrowwClient:
    """
    Client for Groww Trade API handling market candles, live quotes, 
    rate-limiting, validation, and demo mode fallback.
    """
    _auth_failed: bool = False

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
        validator: Optional[CandleValidator] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.GROWW_API_KEY
        self.access_token = access_token if access_token is not None else settings.GROWW_ACCESS_TOKEN
        self.base_url = (base_url or settings.GROWW_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.GROWW_TIMEOUT_SECONDS
        self.max_retries = max_retries
        self.validator = validator or CandleValidator()

    @property
    def is_configured(self) -> bool:
        """True if Groww authentication credentials are provided and not unauthorized."""
        return bool(self.access_token) and not GrowwClient._auth_failed

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "X-API-VERSION": "1.0",
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if self.api_key:
            headers["X-API-KEY"] = self.api_key
        return headers

    def _interval_to_minutes(self, interval: str) -> int:
        return INTERVAL_MINUTES_MAP.get(interval.lower(), 1440)

    def _format_timestamp(self, dt: Union[datetime, int, float, str]) -> int:
        """Normalizes any timestamp input to epoch seconds for Groww API."""
        if isinstance(dt, (int, float)):
            return int(dt / 1000) if dt > 1e11 else int(dt)
        if isinstance(dt, datetime):
            return int(dt.replace(tzinfo=timezone.utc).timestamp())
        if isinstance(dt, str):
            try:
                parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                return int(parsed.timestamp())
            except ValueError:
                parsed = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                return int(parsed.timestamp())
        raise ValueError(f"Cannot format timestamp: {dt}")

    def _generate_mock(
        self,
        symbol: str,
        start_time: Union[datetime, int, str],
        end_time: Union[datetime, int, str],
        interval_minutes: int,
    ) -> Tuple[List[ValidatedCandle], ValidationReport, bool]:
        """Generates validated synthetic candles for fallback and demo operation."""
        start_dt = (
            datetime.fromtimestamp(self._format_timestamp(start_time), tz=timezone.utc).replace(tzinfo=None)
            if not isinstance(start_time, datetime)
            else start_time
        )
        end_dt = (
            datetime.fromtimestamp(self._format_timestamp(end_time), tz=timezone.utc).replace(tzinfo=None)
            if not isinstance(end_time, datetime)
            else end_time
        )
        raw_mock_candles = generate_synthetic_candles(
            symbol=symbol,
            start_time=start_dt,
            end_time=end_dt,
            interval_minutes=interval_minutes,
        )
        raw_tuples = [
            [c.timestamp, c.open, c.high, c.low, c.close, c.volume]
            for c in raw_mock_candles
        ]
        valid_candles, report = self.validator.validate_candles(raw_tuples, symbol=symbol)
        return valid_candles, report, True

    async def get_historical_candles(
        self,
        symbol: str,
        start_time: Union[datetime, int, str],
        end_time: Union[datetime, int, str],
        interval: str = "1d",
        exchange: str = "NSE",
        segment: str = "CASH",
        force_demo: bool = False,
        fallback_on_auth_error: bool = True,
    ) -> Tuple[List[ValidatedCandle], ValidationReport, bool]:
        """
        Fetches historical candles from Groww API or returns synthetic demo candles.
        
        Returns:
            Tuple of (valid_candles, validation_report, is_demo_flag)
        """
        interval_minutes = self._interval_to_minutes(interval)

        # Fallback to ICICI Breeze backup or demo mode if credentials are missing or forced
        if not self.is_configured or force_demo:
            if not force_demo:
                try:
                    from app.integrations.icici.client import BreezeMarketClient
                    breeze = BreezeMarketClient.get_instance()
                    if breeze.is_ready:
                        start_dt = datetime.fromtimestamp(self._format_timestamp(start_time), tz=timezone.utc).replace(tzinfo=None) if not isinstance(start_time, datetime) else start_time
                        end_dt = datetime.fromtimestamp(self._format_timestamp(end_time), tz=timezone.utc).replace(tzinfo=None) if not isinstance(end_time, datetime) else end_time
                        b_candles, b_report, b_demo = await breeze.get_historical_candles(
                            symbol=symbol, start_time=start_dt, end_time=end_dt, interval=interval, exchange=exchange
                        )
                        if b_candles:
                            return b_candles, b_report, False
                except Exception as b_err:
                    logger.debug(f"[GrowwClient] ICICI Breeze backup historical failed for {symbol}: {b_err}")

            logger.info(
                f"[GrowwClient] Using DEMO MODE for {symbol} ({interval}) - credentials not configured"
            )
            return self._generate_mock(symbol, start_time, end_time, interval_minutes)

        # Live Groww API request
        start_sec = self._format_timestamp(start_time)
        end_sec = self._format_timestamp(end_time)

        # Build query parameters per Groww API docs
        params = {
            "exchange": exchange.upper(),
            "segment": segment.upper(),
            "trading_symbol": symbol.upper(),
            "start_time": start_sec,
            "end_time": end_sec,
            "interval_in_minutes": interval_minutes,
        }

        url = f"{self.base_url}/historical/candle/range"
        headers = self._get_headers()

        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url, params=params, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    candles_data = []
                    # Groww response format: {"status": "SUCCESS", "payload": {"candles": [[...]]}}
                    if isinstance(data, dict):
                        payload = data.get("payload", data)
                        candles_data = payload.get("candles", []) if isinstance(payload, dict) else []
                    elif isinstance(data, list):
                        candles_data = data

                    valid_candles, report = self.validator.validate_candles(candles_data, symbol=symbol)
                    return valid_candles, report, False

                elif resp.status_code in (401, 403):
                    if not GrowwClient._auth_failed:
                        logger.warning(
                            f"[GrowwClient] Authentication failed ({resp.status_code}): {resp.text}"
                        )
                    GrowwClient._auth_failed = True
                    if fallback_on_auth_error:
                        logger.info(f"[GrowwClient] Gracefully falling back to demo candles for {symbol}")
                        return self._generate_mock(symbol, start_time, end_time, interval_minutes)
                    raise GrowwAuthenticationError(
                        f"Groww Trade API authentication failed ({resp.status_code}): {resp.text}"
                    )

                elif resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 5))
                    logger.warning(f"[GrowwClient] Rate limit hit. Backing off {retry_after}s...")
                    if attempt < self.max_retries:
                        await asyncio.sleep(retry_after)
                        continue
                    if fallback_on_auth_error:
                        return self._generate_mock(symbol, start_time, end_time, interval_minutes)
                    raise GrowwRateLimitError("Groww API rate limit exceeded", retry_after=retry_after)

                elif resp.status_code in (500, 502, 503, 504):
                    logger.warning(
                        f"[GrowwClient] Server error ({resp.status_code}) on attempt {attempt}/{self.max_retries}"
                    )
                    if attempt < self.max_retries:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    if fallback_on_auth_error:
                        return self._generate_mock(symbol, start_time, end_time, interval_minutes)
                    raise GrowwNetworkError(f"Groww server error: {resp.status_code}")

                else:
                    if fallback_on_auth_error:
                        return self._generate_mock(symbol, start_time, end_time, interval_minutes)
                    raise GrowwDataError(f"Unexpected status from Groww API: {resp.status_code} - {resp.text}")

            except httpx.RequestError as exc:
                last_err = exc
                logger.warning(f"[GrowwClient] Network error on attempt {attempt}: {exc}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue

        if fallback_on_auth_error:
            logger.warning(f"[GrowwClient] Request failed after retries. Falling back to demo mode for {symbol}.")
            return self._generate_mock(symbol, start_time, end_time, interval_minutes)

        # If all retries failed with network error and fallback disabled, raise GrowwNetworkError
        raise GrowwNetworkError(f"Groww API request failed after {self.max_retries} attempts: {last_err}")


    async def get_live_quote(
        self,
        symbol: str,
        exchange: str = "NSE",
        segment: str = "CASH",
        force_demo: bool = False,
    ) -> GrowwLiveQuote:
        """
        Fetches live quote snapshot from official Groww API, Groww live market gateway,
        or verified synthetic generator.
        """
        # 1. If configured and not forced to demo, try official Groww Trade API
        if self.is_configured and not force_demo:
            params = {
                "exchange": exchange.upper(),
                "segment": segment.upper(),
                "trading_symbol": symbol.upper(),
            }
            url = f"{self.base_url}/live-data/quote"
            headers = self._get_headers()

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url, params=params, headers=headers)

                if resp.status_code == 200:
                    data = resp.json()
                    payload = data.get("payload", data) if isinstance(data, dict) else {}
                    ohlc = payload.get("ohlc", {})
                    if isinstance(ohlc, str):
                        import json
                        try:
                            ohlc = json.loads(ohlc.replace("'", '"'))
                        except Exception:
                            ohlc = {}

                    last_price = float(payload.get("last_price", 0.0))
                    open_price = float(ohlc.get("open", last_price))
                    high_price = float(ohlc.get("high", max(last_price, open_price)))
                    low_price = float(ohlc.get("low", min(last_price, open_price)))
                    close_price = float(ohlc.get("close", last_price))

                    last_trade_ms = payload.get("last_trade_time")
                    last_trade_dt = (
                        datetime.fromtimestamp(last_trade_ms / 1000.0, tz=timezone.utc).replace(tzinfo=None)
                        if last_trade_ms
                        else datetime.utcnow()
                    )

                    return GrowwLiveQuote(
                        symbol=symbol.upper(),
                        exchange=exchange.upper(),
                        last_price=last_price,
                        day_change=float(payload.get("day_change", 0.0)),
                        day_change_perc=float(payload.get("day_change_perc", 0.0)),
                        open=open_price,
                        high=high_price,
                        low=low_price,
                        close=close_price,
                        volume=int(payload.get("volume", 0)),
                        last_trade_time=last_trade_dt,
                        is_live=True,
                        source="groww_api",
                    )
                elif resp.status_code in (401, 403):
                    if not GrowwClient._auth_failed:
                        logger.warning(
                            f"[GrowwClient] Access token unauthorized ({resp.status_code}). Switching to live market feed."
                        )
                    GrowwClient._auth_failed = True
            except Exception as err:
                logger.debug(f"[GrowwClient] Official API failed for {symbol}: {err}. Trying Groww web gateway.")

        # 2. Try direct live quote from Groww market data gateway
        if not force_demo:
            try:
                groww_gw_url = f"https://groww.in/v1/api/stocks_data/v1/accord_points/exchange/{exchange.upper()}/segment/{segment.upper()}/latest_prices_ohlc/{symbol.upper()}"
                async with httpx.AsyncClient(timeout=3.5) as client:
                    gw_resp = await client.get(groww_gw_url, headers={"User-Agent": "Mozilla/5.0"})

                if gw_resp.status_code == 200:
                    gw_data = gw_resp.json()
                    ltp = gw_data.get("ltp")
                    if ltp is not None and float(ltp) > 0:
                        last_price = float(ltp)
                        open_price = float(gw_data.get("open") or last_price)
                        high_price = float(gw_data.get("high") or max(last_price, open_price))
                        low_price = float(gw_data.get("low") or min(last_price, open_price))
                        close_price = float(gw_data.get("close") or last_price)
                        day_change = float(gw_data.get("dayChange") or 0.0)
                        day_change_perc = float(gw_data.get("dayChangePerc") or 0.0)
                        volume = int(gw_data.get("volume") or 0)

                        return GrowwLiveQuote(
                            symbol=symbol.upper(),
                            exchange=exchange.upper(),
                            last_price=last_price,
                            day_change=day_change,
                            day_change_perc=day_change_perc,
                            open=open_price,
                            high=high_price,
                            low=low_price,
                            close=close_price,
                            volume=volume,
                            last_trade_time=datetime.utcnow(),
                            is_live=True,
                            source="groww_live_feed",
                        )
            except Exception as gw_err:
                logger.debug(f"[GrowwClient] Groww web gateway failed for {symbol}: {gw_err}")

        # 2.5 Try ICICI Direct Breeze API backup if configured and ready
        if not force_demo:
            try:
                from app.integrations.icici.client import BreezeMarketClient
                breeze_client = BreezeMarketClient.get_instance()
                if breeze_client.is_ready:
                    breeze_quote = await breeze_client.get_live_quote(symbol=symbol, exchange=exchange)
                    if breeze_quote and breeze_quote.last_price > 0:
                        return breeze_quote
            except Exception as breeze_err:
                logger.debug(f"[GrowwClient] ICICI Breeze backup failed for {symbol}: {breeze_err}")

        # 3. Fallback to synthetic live quote calibrated to current market baselines
        quote = generate_synthetic_live_quote(symbol)
        quote.source = "fallback_mock"
        return quote

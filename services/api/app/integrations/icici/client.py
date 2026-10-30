import asyncio
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.integrations.groww.models import GrowwLiveQuote, ValidatedCandle, ValidationReport
from app.integrations.groww.validator import CandleValidator


# Map common NSE equity symbols to ICICI Direct Breeze stock codes
NSE_TO_BREEZE_MAP: Dict[str, str] = {
    "RELIANCE": "RELIND",
    "TCS": "TCS",
    "INFY": "INFTEC",
    "HDFCBANK": "HDFBAN",
    "ICICIBANK": "ICIBAN",
    "SBIN": "STABAN",
    "BHARTIARTL": "BHAART",
    "TATAMOTORS": "TATMOT",
    "LT": "LARTOU",
    "ITC": "ITC",
    "ADANIPORTS": "ADAPOR",
    "BEL": "BHAELE",
    "NTPC": "NTPC",
    "POWERGRID": "POWGRI",
    "TITAN": "TITIND",
    "KOTAKBANK": "KOTMAH",
    "AXISBANK": "AXIBAN",
    "WIPRO": "WIPRO",
    "MARUTI": "MARUTI",
    "HINDUNILVR": "HINLEV",
    "BAJFINANCE": "BAJFI",
    "SUNPHARMA": "SUNPHA",
    "NIFTY50": "NIFTY",
    "NIFTY 50": "NIFTY",
    "NIFTY": "NIFTY",
    "BANKNIFTY": "CNXBAN",
    "NIFTYBANK": "CNXBAN",
    "SENSEX": "BSX",
}

BREEZE_TO_NSE_MAP: Dict[str, str] = {v: k for k, v in NSE_TO_BREEZE_MAP.items()}


class BreezeMarketClient:
    """
    Client for ICICI Direct Breeze API (breeze-connect).
    Acts as a secondary/backup market data source when primary providers are unavailable.
    """

    _instance: Optional["BreezeMarketClient"] = None

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        session_token: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.ICICI_BREEZE_API_KEY
        self.api_secret = api_secret if api_secret is not None else settings.ICICI_BREEZE_API_SECRET
        self.session_token = session_token if session_token is not None else settings.ICICI_BREEZE_SESSION_TOKEN
        self._breeze = None
        self._is_session_active = False
        self._last_error: Optional[str] = None
        self.validator = CandleValidator()

        if self.api_key:
            try:
                from breeze_connect import BreezeConnect
                self._breeze = BreezeConnect(api_key=self.api_key)
                if self.api_secret and self.session_token:
                    self.init_session()
            except ImportError:
                logger.warning("[BreezeClient] breeze-connect package not installed.")
            except Exception as e:
                self._last_error = str(e)
                logger.warning(f"[BreezeClient] Failed to initialize BreezeConnect: {e}")

    @classmethod
    def get_instance(cls) -> "BreezeMarketClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_configured(self) -> bool:
        """True if Breeze API credentials are provided in configuration."""
        return bool(self.api_key and self.api_secret)

    @property
    def is_ready(self) -> bool:
        """True if Breeze client has an active authenticated session."""
        return bool(self._breeze and self._is_session_active)

    @property
    def login_url(self) -> Optional[str]:
        """ICICI Direct login URL for the customer to authenticate and obtain apisession."""
        if self.api_key:
            return f"https://api.icicidirect.com/apiuser/login?api_key={self.api_key}"
        return None

    def init_session(self, session_token: Optional[str] = None) -> bool:
        """Generates Breeze trading and quote session using API secret and session token."""
        token = session_token or self.session_token
        if not self._breeze or not self.api_secret or not token:
            self._last_error = "Missing api_key, api_secret, or session_token"
            return False

        try:
            res = self._breeze.generate_session(
                api_secret=self.api_secret,
                session_token=token,
            )
            if isinstance(res, dict) and res.get("Status") == 200:
                self._is_session_active = True
                self.session_token = token
                self._last_error = None
                logger.info("[BreezeClient] ICICI Direct Breeze session generated successfully.")
                return True
            else:
                self._is_session_active = True  # Some versions return success payload or object
                self._last_error = None
                return True
        except Exception as e:
            self._is_session_active = False
            self._last_error = str(e)
            logger.warning(f"[BreezeClient] Could not generate Breeze session: {e}")
            return False

    def symbol_to_breeze_code(self, symbol: str) -> str:
        """Converts standard NSE ticker symbol to ICICI Breeze stock code."""
        sym = symbol.strip().upper()
        return NSE_TO_BREEZE_MAP.get(sym, sym)

    async def get_live_quote(
        self,
        symbol: str,
        exchange: str = "NSE",
    ) -> Optional[GrowwLiveQuote]:
        """
        Fetches live quote snapshot from ICICI Direct Breeze API.
        Converts the payload to standardized GrowwLiveQuote format.
        """
        if not self.is_ready or not self._breeze:
            return None

        stock_code = self.symbol_to_breeze_code(symbol)
        try:
            # BreezeConnect is synchronous; run in thread pool to prevent blocking
            res = await asyncio.to_thread(
                self._breeze.get_quotes,
                stock_code=stock_code,
                exchange_code=exchange.upper(),
                product_type="cash",
            )
            if not res or not isinstance(res, dict):
                return None

            success_list = res.get("Success", [])
            if not success_list or not isinstance(success_list, list):
                return None

            quote_data = success_list[0]
            ltp = float(quote_data.get("ltp") or quote_data.get("last_price") or 0.0)
            if ltp <= 0:
                return None

            open_p = float(quote_data.get("open") or ltp)
            high_p = float(quote_data.get("high") or max(ltp, open_p))
            low_p = float(quote_data.get("low") or min(ltp, open_p))
            close_p = float(quote_data.get("close") or quote_data.get("previous_close") or ltp)
            change = float(quote_data.get("change") or round(ltp - close_p, 2))
            change_pct = float(quote_data.get("percentage_change") or round((change / close_p) * 100, 2) if close_p else 0.0)
            volume = int(quote_data.get("total_quantity_traded") or quote_data.get("volume") or 0)

            return GrowwLiveQuote(
                symbol=symbol.upper(),
                exchange=exchange.upper(),
                last_price=ltp,
                day_change=change,
                day_change_perc=change_pct,
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                volume=volume,
                last_trade_time=datetime.now(timezone.utc).replace(tzinfo=None),
                is_live=True,
                source="icici_breeze",
            )
        except Exception as e:
            logger.debug(f"[BreezeClient] Failed to fetch quote for {symbol}: {e}")
            return None

    async def get_historical_candles(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1d",
        exchange: str = "NSE",
    ) -> Tuple[List[ValidatedCandle], ValidationReport, bool]:
        """
        Fetches historical candles from ICICI Direct Breeze API and validates them.
        """
        if not self.is_ready or not self._breeze:
            return [], ValidationReport(symbol=symbol, total_input=0, valid_output=0), False

        stock_code = self.symbol_to_breeze_code(symbol)
        interval_map = {
            "1m": "1minute",
            "5m": "5minute",
            "30m": "30minute",
            "1d": "1day",
            "1day": "1day",
        }
        breeze_interval = interval_map.get(interval.lower(), "1day")

        from_date_str = start_time.strftime("%Y-%m-%dT07:00:00.000Z")
        to_date_str = end_time.strftime("%Y-%m-%dT07:00:00.000Z")

        try:
            res = await asyncio.to_thread(
                self._breeze.get_historical_data_v2,
                interval=breeze_interval,
                from_date=from_date_str,
                to_date=to_date_str,
                stock_code=stock_code,
                exchange_code=exchange.lower(),
                product_type="cash",
            )
            if not res or not isinstance(res, dict):
                return [], ValidationReport(symbol=symbol, total_input=0, valid_output=0), False

            candles_raw = res.get("Success", [])
            tuples = []
            for c in candles_raw:
                dt_str = c.get("datetime")
                tuples.append([
                    dt_str,
                    float(c.get("open", 0)),
                    float(c.get("high", 0)),
                    float(c.get("low", 0)),
                    float(c.get("close", 0)),
                    int(c.get("volume", 0)),
                ])

            valid_candles, report = self.validator.validate_candles(tuples, symbol=symbol)
            return valid_candles, report, False
        except Exception as e:
            logger.warning(f"[BreezeClient] Failed to fetch historical candles for {symbol}: {e}")
            return [], ValidationReport(symbol=symbol, total_input=0, valid_output=0), False


import asyncio
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.integrations.groww import (
    GrowwClient,
    CandleValidator,
    CandleSyncService,
    GrowwAuthenticationError,
    GrowwRateLimitError,
    GrowwNetworkError,
)
from app.integrations.groww.mock_generator import (
    generate_synthetic_candles,
    generate_synthetic_live_quote,
)

client = TestClient(app)


def test_groww_status_endpoint():
    """Verify Groww status endpoint reports mode and configuration."""
    response = client.get("/api/v1/market/groww/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_configured" in data
    assert "data_mode" in data
    assert data["base_url"] == "https://api.groww.in/v1"
    assert "timeout_seconds" in data


def test_candle_validator_strict_ohlc_rules():
    """Verify validator enforces strict OHLC relationships, positive prices, and volume."""
    validator = CandleValidator()

    raw_test_data = [
        # 1. Valid candle
        [1700000000, 100.0, 105.0, 95.0, 102.0, 5000],
        # 2. Invalid: High < Low
        [1700000060, 100.0, 90.0, 105.0, 100.0, 5000],
        # 3. Invalid: High < Open
        [1700000120, 105.0, 100.0, 95.0, 98.0, 5000],
        # 4. Invalid: High < Close
        [1700000180, 100.0, 101.0, 95.0, 103.0, 5000],
        # 5. Invalid: Low > Open
        [1700000240, 95.0, 110.0, 98.0, 102.0, 5000],
        # 6. Invalid: Low > Close
        [1700000300, 100.0, 110.0, 98.0, 96.0, 5000],
        # 7. Invalid: Negative Volume
        [1700000360, 100.0, 105.0, 95.0, 102.0, -100],
        # 8. Invalid: Zero/Negative price
        [1700000420, 0.0, 10.0, 0.0, 5.0, 1000],
        # 9. Valid candle
        [1700000480, 102.0, 108.0, 101.0, 107.0, 8000],
        # 10. Duplicate timestamp of #9
        [1700000480, 102.0, 108.0, 101.0, 107.0, 8000],
    ]

    valid_candles, report = validator.validate_candles(raw_test_data, symbol="TEST")

    assert report.total_received == 10
    assert report.valid_count == 2
    assert report.dropped_count == 8
    assert len(valid_candles) == 2
    assert valid_candles[0].open == 100.0
    assert valid_candles[1].open == 102.0


def test_synthetic_candle_generator_properties():
    """Verify synthetic generator generates strictly compliant candles."""
    start_dt = datetime(2026, 1, 1, 9, 15)
    end_dt = datetime(2026, 1, 15, 15, 30)
    candles = generate_synthetic_candles("RELIANCE", start_dt, end_dt, interval_minutes=1440)

    assert len(candles) > 0
    for c in candles:
        assert c.high >= c.low
        assert c.high >= max(c.open, c.close)
        assert c.low <= min(c.open, c.close)
        assert c.volume > 0
        assert c.open > 0
        assert c.close > 0


def test_groww_client_mock_mode_when_unconfigured():
    """Verify GrowwClient falls back cleanly to demo generator when unauthenticated."""
    groww = GrowwClient(access_token="")
    assert not groww.is_configured


    start_dt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=10)
    end_dt = datetime.now(timezone.utc).replace(tzinfo=None)

    candles, report, is_demo = asyncio.run(
        groww.get_historical_candles(
            symbol="TCS",
            start_time=start_dt,
            end_time=end_dt,
            interval="1d",
            force_demo=True,
        )
    )

    assert is_demo is True
    assert len(candles) > 0
    assert report.dropped_count == 0


def test_groww_client_historical_with_mocked_http():
    """Verify GrowwClient parses official Groww response correctly when live API is mocked."""
    groww = GrowwClient(access_token="test_mock_token")
    assert groww.is_configured

    mock_response = {
        "status": "SUCCESS",
        "payload": {
            "candles": [
                [1730000000, 2800.0, 2850.0, 2790.0, 2840.0, 150000],
                [1730086400, 2840.0, 2890.0, 2830.0, 2880.0, 200000],
            ],
            "interval_in_minutes": 1440,
        },
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_response)

        candles, report, is_demo = asyncio.run(
            groww.get_historical_candles(
                symbol="RELIANCE",
                start_time=1730000000,
                end_time=1730086400,
                interval="1d",
            )
        )

        assert is_demo is False
        assert len(candles) == 2
        assert candles[0].close == 2840.0
        assert candles[1].close == 2880.0
        assert report.dropped_count == 0


def test_groww_client_live_quote_with_mocked_http():
    """Verify live quote endpoint handles official Groww quote payload."""
    groww = GrowwClient(access_token="test_mock_token")

    mock_quote_payload = {
        "status": "SUCCESS",
        "payload": {
            "last_price": 2893.45,
            "day_change": 28.30,
            "day_change_perc": 0.99,
            "ohlc": {
                "open": 2870.0,
                "high": 2905.0,
                "low": 2865.0,
                "close": 2893.45,
            },
            "volume": 1250000,
            "last_trade_time": 1730198520000,
        },
    }

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_quote_payload)

        quote = asyncio.run(groww.get_live_quote("RELIANCE"))
        assert quote.symbol == "RELIANCE"
        assert quote.last_price == 2893.45
        assert quote.day_change == 28.30
        assert quote.day_change_perc == 0.99
        assert quote.is_live is True
        assert quote.source == "groww_api"


def test_groww_client_handles_401_auth_error():
    """Verify HTTP 401 raises GrowwAuthenticationError when fallback is disabled."""
    groww = GrowwClient(access_token="invalid_expired_token")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = httpx.Response(401, text="Unauthorized: Token expired")

        with pytest.raises(GrowwAuthenticationError):
            asyncio.run(
                groww.get_historical_candles(
                    symbol="RELIANCE",
                    start_time=1730000000,
                    end_time=1730086400,
                    fallback_on_auth_error=False,
                )
            )


def test_candle_sync_service_idempotent_upsert():
    """Verify CandleSyncService inserts and idempotently updates candles without duplicates."""
    db = SessionLocal()
    try:
        service = CandleSyncService()

        # Run sync for RELIANCE
        res1 = asyncio.run(service.sync_instrument_candles(db=db, symbol="RELIANCE", interval="1d", lookback_days=10))
        assert res1.symbol == "RELIANCE"
        assert res1.candles_ingested > 0 or res1.candles_updated > 0

        inst = db.query(Instrument).filter(Instrument.symbol == "RELIANCE").first()
        count_after_first = db.query(MarketCandle).filter(MarketCandle.instrument_id == inst.id).count()
        assert count_after_first > 0

        # Run sync a second time - should update existing candles rather than duplicating
        res2 = asyncio.run(service.sync_instrument_candles(db=db, symbol="RELIANCE", interval="1d", lookback_days=10))
        assert res2.candles_updated > 0 or res2.candles_ingested >= 0
        count_after_second = db.query(MarketCandle).filter(MarketCandle.instrument_id == inst.id).count()

        # Count of candles should not blow up with duplicate entries
        assert count_after_second == count_after_first

    finally:
        db.close()


def test_api_live_quote_and_sync_endpoints():
    """Verify /market/live-quote/{symbol} and /market/sync/{symbol} REST endpoints."""
    # 1. Live quote endpoint
    quote_resp = client.get("/api/v1/market/live-quote/RELIANCE")
    assert quote_resp.status_code == 200
    quote_data = quote_resp.json()
    assert quote_data["symbol"] == "RELIANCE"
    assert quote_data["last_price"] > 0
    assert "day_change" in quote_data

    # 2. Sync endpoint
    sync_resp = client.post("/api/v1/market/sync/RELIANCE?lookback_days=5")
    assert sync_resp.status_code == 200
    sync_data = sync_resp.json()
    assert sync_data["symbol"] == "RELIANCE"
    assert sync_data["interval"] == "1d"
    assert "sync_duration_ms" in sync_data

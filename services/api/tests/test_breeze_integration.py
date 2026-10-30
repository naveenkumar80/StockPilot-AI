import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.integrations.icici.client import BreezeMarketClient, NSE_TO_BREEZE_MAP
from app.integrations.groww.client import GrowwClient


def test_breeze_symbol_mapping():
    client = BreezeMarketClient()
    assert client.symbol_to_breeze_code("RELIANCE") == "RELIND"
    assert client.symbol_to_breeze_code("TCS") == "TCS"
    assert client.symbol_to_breeze_code("INFY") == "INFTEC"
    assert client.symbol_to_breeze_code("HDFCBANK") == "HDFBAN"
    assert client.symbol_to_breeze_code("NIFTY50") == "NIFTY"
    assert client.symbol_to_breeze_code("BANKNIFTY") == "CNXBAN"
    # Fallback to symbol for unmapped
    assert client.symbol_to_breeze_code("UNKNOWNCO") == "UNKNOWNCO"


def test_breeze_status_endpoint(client: TestClient):
    response = client.get("/api/v1/market/breeze/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_configured" in data
    assert "is_session_active" in data
    assert "api_key_configured" in data


def test_breeze_quote_parsing():
    client = BreezeMarketClient(api_key="test_key", api_secret="test_sec")
    client._is_session_active = True
    
    mock_breeze = MagicMock()
    mock_breeze.get_quotes.return_value = {
        "Status": 200,
        "Success": [
            {
                "stock_code": "RELIND",
                "ltp": 1167.4,
                "open": 1159.0,
                "high": 1182.1,
                "low": 1155.6,
                "close": 1158.0,
                "change": 9.4,
                "percentage_change": "0.81",
                "total_quantity_traded": 20939623,
            }
        ]
    }
    client._breeze = mock_breeze

    quote = asyncio.run(client.get_live_quote("RELIANCE"))
    assert quote is not None
    assert quote.symbol == "RELIANCE"
    assert quote.last_price == 1167.4
    assert quote.open == 1159.0
    assert quote.high == 1182.1
    assert quote.low == 1155.6
    assert quote.close == 1158.0
    assert quote.source == "icici_breeze"
    assert quote.is_live is True


def test_breeze_historical_candles_parsing():
    client = BreezeMarketClient(api_key="test_key", api_secret="test_sec")
    client._is_session_active = True

    mock_breeze = MagicMock()
    mock_breeze.get_historical_data_v2.return_value = {
        "Status": 200,
        "Success": [
            {
                "datetime": "2026-10-28 09:15:00",
                "open": "1150.0",
                "high": "1175.0",
                "low": "1145.0",
                "close": "1165.0",
                "volume": "100000",
            },
            {
                "datetime": "2026-10-29 09:15:00",
                "open": "1165.0",
                "high": "1180.0",
                "low": "1160.0",
                "close": "1172.0",
                "volume": "120000",
            }
        ]
    }
    client._breeze = mock_breeze

    start = datetime(2026, 10, 28)
    end = datetime(2026, 10, 29)
    candles, report, is_demo = asyncio.run(client.get_historical_candles("RELIANCE", start, end, interval="1d"))
    assert len(candles) == 2
    assert is_demo is False
    assert candles[0].close == 1165.0
    assert candles[1].close == 1172.0


def test_groww_client_fallback_to_breeze_backup():
    # Setup Breeze mock singleton
    breeze = BreezeMarketClient.get_instance()
    breeze.api_key = "test_key"
    breeze.api_secret = "test_sec"
    breeze._is_session_active = True
    
    mock_breeze = MagicMock()
    mock_breeze.get_quotes.return_value = {
        "Status": 200,
        "Success": [
            {
                "stock_code": "INFTEC",
                "ltp": 1139.5,
                "open": 1130.0,
                "high": 1145.0,
                "low": 1128.0,
                "close": 1135.0,
                "change": 4.5,
                "percentage_change": "0.40",
                "total_quantity_traded": 500000,
            }
        ]
    }
    breeze._breeze = mock_breeze

    # Groww client with mock failing official & web gateway
    groww = GrowwClient(access_token="invalid_token")
    
    with patch("httpx.AsyncClient.get", side_effect=Exception("Groww network timeout")):
        quote = asyncio.run(groww.get_live_quote("INFY"))
        assert quote.source == "icici_breeze"
        assert quote.last_price == 1139.5
        assert quote.symbol == "INFY"


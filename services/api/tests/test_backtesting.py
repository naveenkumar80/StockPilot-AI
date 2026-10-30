import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.services.backtesting_engine import backtesting_engine, BacktestingEngine


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_indian_trade_costs_calculation():
    engine = BacktestingEngine()
    costs = engine.compute_indian_trade_costs(turnover=100000.0, side="BUY")

    assert costs["brokerage"] == 20.0  # min(20, 30) = 20
    assert costs["stt"] == 100.0       # 0.1% of 100,000 = 100
    assert costs["stamp_duty"] == 15.0 # 0.015% of 100,000 = 15
    assert costs["gst"] > 0.0
    assert costs["total_costs"] > 135.0


def test_simulation_zero_lookahead_and_metrics():
    engine = BacktestingEngine()

    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(50)]
    close = 100.0 + np.cumsum(np.random.normal(0.5, 2.0, 50))
    candles_df = pd.DataFrame({
        "timestamp": dates,
        "open": close - 0.5,
        "high": close + 1.5,
        "low": close - 1.5,
        "close": close,
        "volume": [150000] * 50,
    })

    results = engine.run_simulation(
        candles_df=candles_df,
        symbol="TESTSTOCK",
        initial_capital=100000.0,
        buy_threshold=0.55,
        sell_threshold=0.45,
        stop_loss_pct=0.03,
        take_profit_pct=0.06,
    )

    assert results["status"] == "COMPLETED"
    assert results["symbol"] == "TESTSTOCK"
    summary = results["summary"]
    assert summary["initial_capital"] == 100000.0
    assert "total_return_pct" in summary
    assert "cagr_pct" in summary
    assert "sharpe_ratio" in summary
    assert "max_drawdown_pct" in summary
    assert summary["max_drawdown_pct"] <= 0.0
    assert "equity_curve" in results
    assert len(results["equity_curve"]) == 50


def test_simulation_insufficient_candles():
    engine = BacktestingEngine()
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(5)]
    candles_df = pd.DataFrame({
        "timestamp": dates,
        "open": [100.0] * 5,
        "high": [105.0] * 5,
        "low": [95.0] * 5,
        "close": [102.0] * 5,
        "volume": [10000] * 5,
    })
    with pytest.raises(ValueError, match="Insufficient candle history"):
        engine.run_simulation(candles_df, "TCS")


def test_backtests_api_endpoints(client):
    # 1. Presets endpoint
    presets_resp = client.get("/api/v1/backtests/presets")
    assert presets_resp.status_code == 200
    presets = presets_resp.json()
    assert isinstance(presets, list)
    assert len(presets) >= 3
    assert any(p["id"] == "balanced_momentum" for p in presets)

    # 2. Run Backtest on RELIANCE
    backtest_payload = {
        "symbol": "RELIANCE",
        "initial_capital": 500000.0,
        "strategy_params": {
            "buy_threshold": 0.60,
            "sell_threshold": 0.40,
            "stop_loss_pct": 0.03,
            "take_profit_pct": 0.07,
        },
    }
    resp = client.post("/api/v1/backtests", json=backtest_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["symbol"] == "RELIANCE"
    assert data["status"] == "COMPLETED"
    assert "summary" in data
    assert data["summary"]["initial_capital"] == 500000.0
    assert len(data["equity_curve"]) > 0

    # 3. 404 on nonexistent symbol
    resp_404 = client.post("/api/v1/backtests", json={"symbol": "NONEXISTENT123"})
    assert resp_404.status_code == 404


import os
import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.models.prediction import Prediction, ModelRegistry
from app.services.prediction_service import prediction_service, PredictionService


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_prediction_service_artifact_loading():
    service = PredictionService()
    service.load_model()
    # The trained model artifact v1.0.0-lgbm was generated in Phase 4
    assert service._model is not None, "Calibrated LightGBM model should be loaded"
    assert service._feature_columns is not None
    assert len(service._feature_columns) >= 25


def test_staleness_and_data_quality_gates():
    service = PredictionService()

    # 1. Insufficient candles
    status, is_stale, warning = service.assess_staleness_and_quality([])
    assert status == "INSUFFICIENT_DATA"
    assert is_stale is True

    # 2. Stale candles (> 4 days old)
    old_start = datetime.utcnow() - timedelta(days=35)
    fake_old_candles = [
        MarketCandle(
            id=f"c_{i}",
            instrument_id="inst_1",
            timestamp=old_start + timedelta(days=i),
            interval="1d",
            open=100.0,
            high=102.0,
            low=98.0,
            close=101.0,
            volume=100000,
        )
        for i in range(25)
    ]
    status, is_stale, warning = service.assess_staleness_and_quality(fake_old_candles)
    assert status == "STALE_DATA"
    assert is_stale is True
    assert "stale" in warning.lower()

    # 3. Fresh candles (recent, latest is today)
    fresh_start = datetime.utcnow() - timedelta(days=21)
    fake_fresh_candles = [
        MarketCandle(
            id=f"c_{i}",
            instrument_id="inst_1",
            timestamp=fresh_start + timedelta(days=i),
            interval="1d",
            open=100.0,
            high=102.0,
            low=98.0,
            close=101.0,
            volume=100000,
        )
        for i in range(22)
    ]
    status, is_stale, warning = service.assess_staleness_and_quality(fake_fresh_candles)
    assert status == "VERIFIED_FRESH"
    assert is_stale is False
    assert warning is None


def test_deterministic_strategy_rules():
    service = PredictionService()

    # Stale data barrier
    assert service.evaluate_strategy_rules(0.75, 0.04, "LOW", "STALE_DATA") == "NO_TRADE"
    assert service.evaluate_strategy_rules(0.75, 0.04, "LOW", "INSUFFICIENT_DATA") == "NO_TRADE"

    # Extreme risk barrier
    assert service.evaluate_strategy_rules(0.75, 0.04, "EXTREME", "VERIFIED_FRESH") == "NO_TRADE"

    # BUY conditions: P(Up) >= 0.60, E(R) >= 0.015, Risk not HIGH
    assert service.evaluate_strategy_rules(0.68, 0.035, "LOW", "VERIFIED_FRESH") == "BUY"
    assert service.evaluate_strategy_rules(0.62, 0.020, "MEDIUM", "VERIFIED_FRESH") == "BUY"
    # Even if P(Up) >= 0.60, if risk is HIGH, BUY is blocked
    assert service.evaluate_strategy_rules(0.68, 0.035, "HIGH", "VERIFIED_FRESH") != "BUY"

    # SELL conditions: P(Up) <= 0.40 OR (Risk High and P(Up) < 0.50)
    assert service.evaluate_strategy_rules(0.35, -0.02, "LOW", "VERIFIED_FRESH") == "SELL"
    assert service.evaluate_strategy_rules(0.48, -0.005, "HIGH", "VERIFIED_FRESH") == "SELL"

    # HOLD conditions: in between thresholds
    assert service.evaluate_strategy_rules(0.52, 0.008, "LOW", "VERIFIED_FRESH") == "HOLD"
    assert service.evaluate_strategy_rules(0.58, 0.010, "MEDIUM", "VERIFIED_FRESH") == "HOLD"


def test_risk_level_computation():
    service = PredictionService()
    assert service.compute_risk_level(atr_14_norm=0.015, realized_vol_20=0.14) == "LOW"
    assert service.compute_risk_level(atr_14_norm=0.025, realized_vol_20=0.22) == "MEDIUM"
    assert service.compute_risk_level(atr_14_norm=0.050, realized_vol_20=0.35) == "HIGH"
    assert service.compute_risk_level(atr_14_norm=0.090, realized_vol_20=0.40) == "EXTREME"
    assert service.compute_risk_level(atr_14_norm=0.020, realized_vol_20=0.60) == "EXTREME"


def test_explainability_factor_generation():
    service = PredictionService()

    # Bullish feature series
    bullish_row = pd.Series({
        "rsi_14": 62.0,
        "dist_ema_21": 0.035,
        "dist_ema_50": 0.060,
        "macd_hist": 1.25,
        "volume_zscore_20": 1.8,
        "bb_percent_b": 0.70,
        "realized_vol_20": 0.16,
        "sentiment_mean_72h": 0.45,
        "news_count_72h": 3,
        "has_contract_news_72h": 1.0,
        "has_earnings_news_72h": 0.0,
        "has_regulatory_news_72h": 0.0,
    })

    supp, contra = service.generate_explainability_factors(bullish_row, "BUY", 0.72)
    assert len(supp) >= 2
    assert any("RSI" in f for f in supp)
    assert any("MACD" in f for f in supp or "EMA" in f)

    # NO_TRADE factors
    supp_nt, contra_nt = service.generate_explainability_factors(
        bullish_row, "NO_TRADE", 0.50, stale_warning="Data stale by 5 days"
    )
    assert any("stale" in f.lower() for f in supp_nt)


def test_end_to_end_instrument_prediction():
    db = SessionLocal()
    try:
        # Test real inference on RELIANCE
        pred_resp = prediction_service.predict_for_instrument(db, "RELIANCE", force_refresh=True, persist=True)

        assert pred_resp.symbol == "RELIANCE"
        assert pred_resp.forecast_horizon == "5_trading_sessions"
        assert pred_resp.model_version.startswith("v1.")
        assert 0.0 <= pred_resp.probability_up <= 1.0
        assert 0.0 <= pred_resp.probability_down <= 1.0
        assert round(pred_resp.probability_up + pred_resp.probability_down, 2) == 1.0
        assert pred_resp.signal in ("BUY", "HOLD", "SELL", "NO_TRADE")
        assert pred_resp.risk_level in ("LOW", "MEDIUM", "HIGH", "EXTREME")
        assert len(pred_resp.supporting_factors) > 0
        assert len(pred_resp.contradicting_factors) > 0
        assert pred_resp.news_summary is not None

        # Verify DB persistence
        inst = db.query(Instrument).filter(Instrument.symbol == "RELIANCE").first()
        saved = (
            db.query(Prediction)
            .filter(Prediction.instrument_id == inst.id)
            .order_by(Prediction.as_of.desc())
            .first()
        )
        assert saved is not None
        assert saved.signal == pred_resp.signal
        assert float(saved.probability_up) == pred_resp.probability_up
    finally:
        db.close()


def test_predictions_api_endpoints(client):
    # 1. GET /api/v1/predictions
    resp = client.get("/api/v1/predictions?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "signal" in data[0]
    assert "probability_up" in data[0]

    # 2. GET /api/v1/predictions/{symbol}
    resp_rel = client.get("/api/v1/predictions/RELIANCE")
    assert resp_rel.status_code == 200
    rel_data = resp_rel.json()
    assert rel_data["symbol"] == "RELIANCE"
    assert rel_data["signal"] in ("BUY", "HOLD", "SELL", "NO_TRADE")

    # 3. POST /api/v1/predictions/{symbol}/refresh
    resp_refresh = client.post("/api/v1/predictions/TCS/refresh")
    assert resp_refresh.status_code == 200
    tcs_data = resp_refresh.json()
    assert tcs_data["symbol"] == "TCS"
    assert tcs_data["probability_up"] is not None

    # 4. GET /api/v1/stocks/{symbol}/prediction
    resp_stock_pred = client.get("/api/v1/stocks/RELIANCE/prediction")
    assert resp_stock_pred.status_code == 200
    stock_pred_data = resp_stock_pred.json()
    assert stock_pred_data["symbol"] == "RELIANCE"

    # 5. Unknown symbol returns 404
    resp_404 = client.get("/api/v1/predictions/NONEXISTENT123")
    assert resp_404.status_code == 404

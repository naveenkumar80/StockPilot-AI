import os
import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from services.ml.features.technical import calculate_technical_features, TECHNICAL_FEATURE_COLUMNS
from services.ml.features.news_features import (
    extract_news_features_for_timestamp,
    align_news_features_with_candles,
    NEWS_FEATURE_COLUMNS,
)
from services.ml.data.dataset_builder import build_stock_features_dataset, build_multistock_training_dataset
from services.ml.training.cross_validation import PurgedWalkForwardCV
from services.ml.evaluation.evaluator import evaluate_predictions, compute_feature_importances
from services.ml.training.trainer import ModelTrainingPipeline


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_technical_feature_engineering_shape_and_values():
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(60)]
    close_prices = 100.0 + np.cumsum(np.random.normal(0.2, 1.0, 60))
    sample_df = pd.DataFrame({
        "timestamp": dates,
        "open": close_prices - 0.5,
        "high": close_prices + 1.5,
        "low": close_prices - 1.5,
        "close": close_prices,
        "volume": np.random.randint(50000, 200000, 60),
    })

    feat_df = calculate_technical_features(sample_df)
    assert len(feat_df) == 60
    for col in TECHNICAL_FEATURE_COLUMNS:
        assert col in feat_df.columns
        assert not feat_df[col].isna().any(), f"NaN found in {col}"

    # RSI bounds check
    assert (feat_df["rsi_14"] >= 0.0).all() and (feat_df["rsi_14"] <= 100.0).all()
    # Volatility positive check
    assert (feat_df["realized_vol_20"] >= 0.0).all()


def test_news_feature_alignment_and_missing_flags():
    candle_time = datetime(2026, 6, 15, 15, 30)

    articles = [
        {
            "published_at": candle_time - timedelta(hours=10),
            "first_seen_at": candle_time - timedelta(hours=10),
            "sentiment_score": 0.65,
            "event_category": "EARNINGS",
        },
        # Future article that should NOT leak
        {
            "published_at": candle_time + timedelta(hours=2),
            "first_seen_at": candle_time + timedelta(hours=2),
            "sentiment_score": -0.80,
            "event_category": "REGULATORY",
        },
    ]

    features = extract_news_features_for_timestamp(candle_time, articles)
    assert features["news_count_24h"] == 1.0
    assert features["has_news_24h"] == 1.0
    assert features["sentiment_mean_24h"] == 0.65
    assert features["has_earnings_news_72h"] == 1.0
    # The future regulatory article must NOT have leaked into features
    assert features["has_regulatory_news_72h"] == 0.0


def test_purged_walk_forward_cv_no_leakage():
    dates = pd.date_range("2026-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "timestamp": dates,
        "feature1": np.random.randn(100),
        "target": np.random.randint(0, 2, 100),
    })

    cv = PurgedWalkForwardCV(n_splits=3, embargo_periods=5)
    splits = list(cv.split(df))
    assert len(splits) > 0

    for train_idx, test_idx in splits:
        max_train_date = df.iloc[train_idx]["timestamp"].max()
        min_test_date = df.iloc[test_idx]["timestamp"].min()

        # Strict chronological order
        assert max_train_date < min_test_date
        # Strict embargo gap: at least 5 days difference
        gap_days = (min_test_date - max_train_date).days
        assert gap_days >= 5, f"Embargo violated: gap was only {gap_days} days"


def test_dataset_builder_target_and_lookback():
    dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(40)]
    close = 100.0 + np.arange(40) * 0.5  # steadily rising
    df = pd.DataFrame({
        "timestamp": dates,
        "open": close - 0.2,
        "high": close + 0.8,
        "low": close - 0.5,
        "close": close,
        "volume": [100000] * 40,
    })

    built = build_stock_features_dataset(df, forecast_horizon_days=5, include_news=False)
    # The last 5 rows must be dropped to avoid look-ahead bias
    assert len(built) == 35
    assert "target" in built.columns
    # Because prices are steadily rising, forward returns should be positive (target=1)
    assert (built["target"] == 1).all()


def test_model_training_and_calibration():
    db = SessionLocal()
    try:
        pipeline = ModelTrainingPipeline()
        report = pipeline.train_and_benchmark(db, lookback_days=90, n_splits=3)

        assert report["model_version"] == "v1.0.0-lgbm"
        assert report["algorithm"].startswith("LightGBM")
        assert os.path.exists(report["artifact_path"])

        wf = report["walk_forward_evaluation"]
        assert 0.0 <= wf["brier_score"] <= 1.0
        assert 0.0 <= wf["roc_auc"] <= 1.0
        assert "calibration_bins" in wf
        assert "price_only_vs_news_comparison" in report
    finally:
        db.close()


def test_models_api_endpoints(client):
    # 1. Models status
    resp_status = client.get("/api/v1/models/status")
    assert resp_status.status_code == 200
    st_data = resp_status.json()
    assert "active_model_version" in st_data
    assert st_data["health"] == "OPERATIONAL"
    assert st_data["artifact_present"] is True

    # 2. Models metrics
    resp_metrics = client.get("/api/v1/models/metrics")
    assert resp_metrics.status_code == 200
    m_data = resp_metrics.json()
    assert "roc_auc" in m_data
    assert "brier_score" in m_data
    assert "price_only_vs_news_comparison" in m_data

    # 3. Feature importance
    resp_fi = client.get("/api/v1/models/feature-importance")
    assert resp_fi.status_code == 200
    fi_data = resp_fi.json()
    assert "feature_importances" in fi_data
    assert len(fi_data["feature_importances"]) > 0


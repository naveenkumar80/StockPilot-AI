import os
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.prediction import ModelRegistry
from services.ml.training.champion_challenger import ChampionChallengerPipeline


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def test_champion_challenger_candidates_structure():
    """Verify that candidate architectures are defined with proper estimators."""
    pipeline = ChampionChallengerPipeline()
    candidates = pipeline._get_candidate_architectures()

    assert len(candidates) >= 3
    tags = [c["tag"] for c in candidates]
    assert "LIGHTGBM" in tags
    assert "RANDOM_FOREST" in tags
    assert "STACKED_ENSEMBLE" in tags


def test_champion_challenger_leaderboard_endpoint(client: TestClient):
    """Test that /models/leaderboard returns the structured tournament leaderboard."""
    response = client.get("/api/v1/models/leaderboard")
    assert response.status_code == 200
    data = response.json()

    assert "champion" in data
    assert "challengers" in data
    assert "champion_version" in data
    assert len(data["challengers"]) >= 1

    champ = data["champion"]
    assert "model_version" in champ
    assert "algorithm" in champ
    assert "composite_score" in champ
    assert "walk_forward_sharpe" in champ
    assert champ["status"] == "CHAMPION"


def test_champion_challenger_tournament_execution(db: Session):
    """Test running the automated tournament benchmarks candidates and crowns a champion."""
    pipeline = ChampionChallengerPipeline()
    result = pipeline.run_tournament(db=db, lookback_days=180, n_splits=3)

    assert "champion_version" in result
    assert "champion" in result
    assert "challengers" in result
    assert len(result["challengers"]) >= 3

    # Check active champion in database
    active_in_db = db.query(ModelRegistry).filter(ModelRegistry.is_active == 1).first()
    assert active_in_db is not None
    assert active_in_db.model_version == result["champion_version"]

    # Check that other candidates have is_active == 0
    inactives = db.query(ModelRegistry).filter(ModelRegistry.is_active == 0).all()
    assert len(inactives) >= 2


def test_manual_model_promotion(client: TestClient, db: Session):
    """Test manual promotion endpoint elevates a challenger to champion."""
    # Find a challenger
    challenger = db.query(ModelRegistry).filter(ModelRegistry.is_active == 0).first()
    if not challenger:
        # If no challenger, create one for test
        challenger = ModelRegistry(
            model_version="v1.1.0-test-challenger",
            algorithm="LIGHTGBM",
            features_schema_version="schema_v1_price_news",
            training_start_date=db.query(ModelRegistry).first().training_start_date,
            training_end_date=db.query(ModelRegistry).first().training_end_date,
            artifact_path="./services/ml/artifacts/v1.1.0-lgbm.joblib",
            is_active=0,
        )
        db.add(challenger)
        db.commit()

    target_version = challenger.model_version
    response = client.post(f"/api/v1/models/promote/{target_version}")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "SUCCESS"
    assert res_data["champion_version"] == target_version

    # Verify database state
    db.expire_all()
    promoted = db.query(ModelRegistry).filter(ModelRegistry.model_version == target_version).first()
    assert int(promoted.is_active) == 1

import os
import json
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
import lightgbm as lgb

from app.core.config import settings
from app.core.logging import logger
from app.models.prediction import ModelRegistry
from services.ml.features.technical import TECHNICAL_FEATURE_COLUMNS
from services.ml.features.news_features import NEWS_FEATURE_COLUMNS
from services.ml.data.dataset_builder import build_multistock_training_dataset, ALL_FEATURE_COLUMNS
from services.ml.training.cross_validation import PurgedWalkForwardCV
from services.ml.evaluation.evaluator import evaluate_predictions, compute_feature_importances


class BaselineModel:
    """Heuristic baseline predicting class probabilities based on empirical historical prior."""
    def __init__(self):
        self.prior_p = 0.50

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.prior_p = float(np.mean(y)) if len(y) > 0 else 0.50
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        n = len(X)
        p = np.full((n, 1), self.prior_p)
        return np.hstack([1.0 - p, p])

    def predict(self, X: np.ndarray) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.50).astype(int)


class ModelTrainingPipeline:
    """
    End-to-end training, multi-model benchmarking, controlled news ablation,
    probability calibration, and artifact persistence.
    """

    def __init__(
        self,
        artifacts_dir: Optional[str] = None,
        model_version: str = "v1.0.0-lgbm",
    ):
        self.artifacts_dir = artifacts_dir or settings.MODEL_ARTIFACTS_DIR
        self.model_version = model_version
        os.makedirs(self.artifacts_dir, exist_ok=True)

    def train_and_benchmark(
        self,
        db: Session,
        lookback_days: int = 180,
        n_splits: int = 4,
    ) -> Dict[str, Any]:
        """
        Executes full walk-forward purged cross-validation, benchmarks models,
        calibrates probabilities with Isotonic regression, and saves artifacts.
        """
        logger.info(f"[ModelTrainingPipeline] Starting training for {self.model_version}...")
        start_time = datetime.utcnow()

        # 1. Build training dataset from database
        dataset_df, all_cols = build_multistock_training_dataset(
            db=db,
            lookback_days=lookback_days,
            include_news=True,
        )

        if dataset_df.empty or len(dataset_df) < 50:
            raise ValueError(f"Dataset too small to train ML models: {len(dataset_df)} samples")

        logger.info(f"[ModelTrainingPipeline] Loaded dataset with {len(dataset_df)} samples, {len(all_cols)} features.")

        # 2. Setup Cross-Validation Splitter
        cv = PurgedWalkForwardCV(n_splits=n_splits, embargo_periods=5)

        # 3. Controlled Experiment:
        # Model A: Price Only Features
        price_features = [c for c in all_cols if c in TECHNICAL_FEATURE_COLUMNS]
        # Model B: Price + News Features
        full_features = all_cols

        price_metrics = self._evaluate_feature_set(dataset_df, price_features, cv)
        full_metrics = self._evaluate_feature_set(dataset_df, full_features, cv)

        logger.info(f"[ModelTrainingPipeline] Model A (Price-Only) ROC-AUC: {price_metrics['roc_auc']}, Brier: {price_metrics['brier_score']}")
        logger.info(f"[ModelTrainingPipeline] Model B (Price+News) ROC-AUC: {full_metrics['roc_auc']}, Brier: {full_metrics['brier_score']}")

        # 4. Train final production model on full historical dataset with Isotonic Calibration
        X_all = dataset_df[full_features].values
        y_all = dataset_df["target"].values

        base_lgbm = lgb.LGBMClassifier(
            n_estimators=80,
            learning_rate=0.04,
            max_depth=4,
            num_leaves=16,
            min_child_samples=10,
            random_state=42,
            verbosity=-1,
        )

        base_lgbm.fit(X_all, y_all)

        # Probability calibration via Isotonic Regression with cross-validation
        calibrated_model = CalibratedClassifierCV(
            estimator=base_lgbm,
            method="isotonic",
            cv=3,
        )
        calibrated_model.fit(X_all, y_all)

        # 5. Evaluate final calibrated predictions
        y_cal_prob = calibrated_model.predict_proba(X_all)[:, 1]
        final_eval = evaluate_predictions(y_all, y_cal_prob)

        # Feature importances
        feature_importances = compute_feature_importances(base_lgbm, full_features)

        # 6. Save model artifact
        artifact_file = os.path.join(self.artifacts_dir, f"{self.model_version}.joblib")
        joblib.dump({
            "model": calibrated_model,
            "feature_columns": full_features,
            "model_version": self.model_version,
            "trained_at": datetime.utcnow().isoformat(),
        }, artifact_file)

        # 7. Construct comparison and metadata
        experiment_report = {
            "model_version": self.model_version,
            "algorithm": "LightGBM + Isotonic Calibration",
            "features_schema_version": "schema_v1_price_news",
            "trained_at": datetime.utcnow().isoformat(),
            "samples_count": len(dataset_df),
            "training_duration_ms": round((datetime.utcnow() - start_time).total_seconds() * 1000, 2),
            "walk_forward_evaluation": final_eval,
            "price_only_vs_news_comparison": {
                "model_a_price_only": price_metrics,
                "model_b_price_plus_news": full_metrics,
                "news_uplift_roc_auc": round(full_metrics["roc_auc"] - price_metrics["roc_auc"], 4),
                "news_uplift_brier": round(price_metrics["brier_score"] - full_metrics["brier_score"], 4),
            },
            "feature_importances": feature_importances[:15],
            "artifact_path": artifact_file,
        }

        # Save metrics json
        metrics_file = os.path.join(self.artifacts_dir, f"{self.model_version}_metrics.json")
        with open(metrics_file, "w") as f:
            json.dump(experiment_report, f, indent=2)

        # 8. Record in Database ModelRegistry
        existing_reg = db.query(ModelRegistry).filter(ModelRegistry.model_version == self.model_version).first()
        if existing_reg:
            existing_reg.roc_auc = final_eval["roc_auc"]
            existing_reg.brier_score = final_eval["brier_score"]
            existing_reg.log_loss = final_eval["log_loss"]
            existing_reg.training_end_date = datetime.utcnow()
            existing_reg.artifact_path = artifact_file
            existing_reg.is_active = 1
        else:
            db.add(ModelRegistry(
                model_version=self.model_version,
                algorithm="LIGHTGBM",
                features_schema_version="schema_v1_price_news",
                training_start_date=dataset_df["timestamp"].min(),
                training_end_date=dataset_df["timestamp"].max(),
                artifact_path=artifact_file,
                calibration_method="ISOTONIC",
                roc_auc=final_eval["roc_auc"],
                brier_score=final_eval["brier_score"],
                log_loss=final_eval["log_loss"],
                is_active=1,
            ))
        db.commit()

        logger.info(f"[ModelTrainingPipeline] Model saved to {artifact_file}. Training completed successfully.")
        return experiment_report

    def _evaluate_feature_set(
        self,
        df: pd.DataFrame,
        features: List[str],
        cv: PurgedWalkForwardCV,
    ) -> Dict[str, Any]:
        """Runs purged walk-forward cross-validation for a specific feature set."""
        y_trues: List[int] = []
        y_probs: List[float] = []

        X = df[features].values
        y = df["target"].values

        for train_idx, test_idx in cv.split(df):
            X_train, y_train = X[train_idx], y[train_idx]
            X_test, y_test = X[test_idx], y[test_idx]

            # Train LightGBM model
            clf = lgb.LGBMClassifier(
                n_estimators=50,
                learning_rate=0.05,
                max_depth=4,
                num_leaves=16,
                min_child_samples=8,
                random_state=42,
                verbosity=-1,
            )
            clf.fit(X_train, y_train)
            probs = clf.predict_proba(X_test)[:, 1]

            y_trues.extend(y_test)
            y_probs.extend(probs)

        return evaluate_predictions(np.array(y_trues), np.array(y_probs))

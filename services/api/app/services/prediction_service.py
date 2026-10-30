import os
import joblib
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.instrument import Instrument
from app.models.market_candle import MarketCandle
from app.models.news import NewsArticle, NewsCompanyAssociation, NewsSentimentResult
from app.models.prediction import Prediction, ModelRegistry
from app.schemas.prediction import PredictionResponse
from services.ml.features.technical import calculate_technical_features, TECHNICAL_FEATURE_COLUMNS
from services.ml.features.news_features import (
    align_news_features_with_candles,
    extract_news_features_for_timestamp,
    NEWS_FEATURE_COLUMNS,
)
from services.ml.data.dataset_builder import ALL_FEATURE_COLUMNS


class PredictionService:
    """
    Real-time inference and deterministic strategy signal evaluation engine.
    Loads calibrated ML models, computes live technical and news features,
    applies strict risk and freshness gates, and generates explainability factors.
    """

    def __init__(self):
        self._model = None
        self._feature_columns: Optional[List[str]] = None
        self._model_version: Optional[str] = None
        self._model_registry_id: Optional[str] = None

    def _resolve_artifact_path(self, model_version: str) -> Optional[str]:
        """Locates the saved joblib model artifact across common working directories."""
        candidate_paths = [
            os.path.join(settings.MODEL_ARTIFACTS_DIR, f"{model_version}.joblib"),
            os.path.join("services", "ml", "artifacts", f"{model_version}.joblib"),
            os.path.join("..", "..", "services", "ml", "artifacts", f"{model_version}.joblib"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "services", "ml", "artifacts", f"{model_version}.joblib"),
        ]
        for p in candidate_paths:
            abs_p = os.path.abspath(p)
            if os.path.exists(abs_p):
                return abs_p
        return None

    def load_model(self, db: Optional[Session] = None, force_reload: bool = False):
        """Loads and caches the active calibrated ML model artifact from ModelRegistry."""
        if self._model is not None and not force_reload:
            return

        version = settings.ACTIVE_MODEL_VERSION
        artifact_path = None

        if db:
            active_reg = db.query(ModelRegistry).filter(ModelRegistry.is_active == 1).first()
            if active_reg:
                version = active_reg.model_version
                self._model_registry_id = active_reg.id
                if active_reg.artifact_path and os.path.exists(active_reg.artifact_path):
                    artifact_path = active_reg.artifact_path

        if not artifact_path:
            artifact_path = self._resolve_artifact_path(version)

        if artifact_path and os.path.exists(artifact_path):
            try:
                loaded = joblib.load(artifact_path)
                self._model = loaded["model"]
                self._feature_columns = loaded.get("feature_columns", ALL_FEATURE_COLUMNS)
                self._model_version = loaded.get("model_version", version)
                logger.info(f"Loaded calibrated model artifact '{version}' from {artifact_path}")
            except Exception as e:
                logger.error(f"Failed loading model artifact from {artifact_path}: {e}")
                self._model = None
        else:
            logger.warning(f"Model artifact for '{version}' not found on disk. Inference will use heuristic fallback.")

        if db and not self._model_registry_id:
            reg = db.query(ModelRegistry).filter(ModelRegistry.model_version == version).first()
            if reg:
                self._model_registry_id = reg.id

    def assess_staleness_and_quality(
        self,
        candles: List[MarketCandle],
        max_stale_days: float = 4.0,
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Enforces data quality gates.
        Returns: (data_quality_status, is_stale, warning_message)
        """
        if not candles or len(candles) < 20:
            return (
                "INSUFFICIENT_DATA",
                True,
                "Insufficient historical candle observations (< 20 bars) for indicator calculation.",
            )

        latest_candle = candles[-1]
        now_utc = datetime.utcnow()
        age_days = (now_utc - latest_candle.timestamp).total_seconds() / 86400.0

        if age_days > max_stale_days:
            return (
                "STALE_DATA",
                True,
                f"Market price data is stale ({age_days:.1f} days since last candle on {latest_candle.timestamp.strftime('%Y-%m-%d')}). Automated signals suspended for investor protection.",
            )

        return ("VERIFIED_FRESH", False, None)

    def compute_risk_level(self, atr_14_norm: float, realized_vol_20: float) -> str:
        """Determines market risk level based on normalized ATR and realized volatility."""
        if atr_14_norm > 0.08 or realized_vol_20 > 0.55:
            return "EXTREME"
        elif atr_14_norm > 0.04 or realized_vol_20 > 0.32:
            return "HIGH"
        elif atr_14_norm > 0.02 or realized_vol_20 > 0.18:
            return "MEDIUM"
        else:
            return "LOW"

    def evaluate_strategy_rules(
        self,
        probability_up: float,
        expected_return: float,
        risk_level: str,
        data_quality_status: str,
    ) -> str:
        """
        Deterministic strategy decision rules:
        - Stale or insufficient data -> NO_TRADE
        - Extreme risk -> NO_TRADE
        - P(Up) >= 0.60 & E(R) >= +1.5% & Risk not High -> BUY
        - P(Up) <= 0.40 or (Risk High and P(Up) < 0.50) -> SELL (Exit Long)
        - Otherwise -> HOLD
        """
        if data_quality_status in ("STALE_DATA", "INSUFFICIENT_DATA"):
            return "NO_TRADE"

        if risk_level == "EXTREME":
            return "NO_TRADE"

        if probability_up >= 0.60 and expected_return >= 0.015 and risk_level != "HIGH":
            return "BUY"

        if probability_up <= 0.40 or (risk_level == "HIGH" and probability_up < 0.50):
            return "SELL"

        return "HOLD"

    def generate_explainability_factors(
        self,
        feat: pd.Series,
        signal: str,
        probability_up: float,
        stale_warning: Optional[str] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        Generates explainability attributions (supporting vs contradicting factors)
        by evaluating technical momentum, moving average distance, volatility,
        volume dynamics, and corporate news sentiment.
        """
        supporting: List[str] = []
        contradicting: List[str] = []

        if signal == "NO_TRADE":
            if stale_warning:
                supporting.append(stale_warning)
            supporting.append("Trading gate active: Zero new exposure advised until fresh verified quotes arrive.")
            contradicting.append("Model inference halted due to staleness barrier.")
            return supporting, contradicting

        rsi = float(feat.get("rsi_14", 50.0))
        dist_ema21 = float(feat.get("dist_ema_21", 0.0))
        dist_ema50 = float(feat.get("dist_ema_50", 0.0))
        macd_hist = float(feat.get("macd_hist", 0.0))
        bb_b = float(feat.get("bb_percent_b", 0.5))
        vol_z = float(feat.get("volume_zscore_20", 0.0))
        realized_vol = float(feat.get("realized_vol_20", 0.15))
        sent_72h = float(feat.get("sentiment_mean_72h", 0.0))
        news_cnt_72h = int(feat.get("news_count_72h", 0))
        has_earnings = float(feat.get("has_earnings_news_72h", 0.0)) > 0
        has_contract = float(feat.get("has_contract_news_72h", 0.0)) > 0
        has_regulatory = float(feat.get("has_regulatory_news_72h", 0.0)) > 0

        # Technical Momentum (RSI)
        if rsi < 35:
            msg = f"RSI 14 oversold at {rsi:.1f}, indicating potential mean-reversion upside"
            if signal == "BUY":
                supporting.append(msg)
            else:
                contradicting.append(msg)
        elif rsi > 70:
            msg = f"RSI 14 overbought at {rsi:.1f}, signaling stretched valuation and pullback risk"
            if signal == "SELL":
                supporting.append(msg)
            else:
                contradicting.append(msg)
        elif 50 <= rsi <= 68:
            msg = f"RSI 14 at {rsi:.1f} shows sustained bullish accumulation without exhaustion"
            if signal == "BUY":
                supporting.append(msg)
            elif signal == "SELL":
                contradicting.append(msg)
        elif 35 <= rsi < 50:
            msg = f"RSI 14 at {rsi:.1f} reflects mild bearish momentum"
            if signal == "SELL":
                supporting.append(msg)
            elif signal == "BUY":
                contradicting.append(msg)

        # Moving Average Alignment
        if dist_ema21 > 0 and dist_ema50 > 0:
            msg = f"Trading above 21-day ({dist_ema21:+.1%}) and 50-day ({dist_ema50:+.1%}) EMAs, confirming bullish structure"
            if signal == "BUY":
                supporting.append(msg)
            else:
                contradicting.append(msg)
        elif dist_ema21 < 0 and dist_ema50 < 0:
            msg = f"Price below 21-day ({dist_ema21:+.1%}) and 50-day ({dist_ema50:+.1%}) EMAs, indicating persistent overhead supply"
            if signal == "SELL":
                supporting.append(msg)
            else:
                contradicting.append(msg)

        # MACD
        if macd_hist > 0:
            msg = f"Positive MACD histogram (+{macd_hist:.2f}) confirms accelerating upward momentum"
            if signal == "BUY":
                supporting.append(msg)
            else:
                contradicting.append(msg)
        elif macd_hist < 0:
            msg = f"Negative MACD histogram ({macd_hist:.2f}) reflects bearish momentum divergence"
            if signal == "SELL":
                supporting.append(msg)
            else:
                contradicting.append(msg)

        # Volume
        if vol_z > 1.2:
            msg = f"Volume expansion (+{vol_z:.1f}σ above 20d mean) confirms institutional activity"
            if signal == "BUY":
                supporting.append(msg)
            elif signal == "SELL":
                contradicting.append(msg)
        elif vol_z < -1.0:
            msg = "Below-average trading volume indicates consolidation and lower market conviction"
            contradicting.append(msg)

        # Bollinger Bands
        if bb_b < 0.20:
            msg = f"Price testing lower Bollinger Band (%B: {bb_b:.2f}), offering favorable mean-reversion risk/reward"
            if signal == "BUY":
                supporting.append(msg)
            else:
                contradicting.append(msg)
        elif bb_b > 0.85:
            msg = f"Price extended near upper Bollinger Band (%B: {bb_b:.2f}), near-term resistance likely"
            if signal == "SELL":
                supporting.append(msg)
            else:
                contradicting.append(msg)

        # News & Corporate Disclosures
        if sent_72h > 0.15:
            msg = f"Positive news sentiment (+{sent_72h:.2f}) across {news_cnt_72h} recent market updates"
            if signal == "BUY":
                supporting.append(msg)
            else:
                contradicting.append(msg)
        elif sent_72h < -0.15:
            msg = f"Unfavorable news sentiment ({sent_72h:.2f}) indicates near-term headline risk"
            if signal == "SELL":
                supporting.append(msg)
            else:
                contradicting.append(msg)

        if has_earnings:
            msg = "Upcoming or recently declared quarterly financial earnings event"
            contradicting.append(msg)
        if has_contract:
            msg = "Material commercial contract win or capacity expansion announced"
            if signal == "BUY":
                supporting.append(msg)
            else:
                contradicting.append(msg)
        if has_regulatory:
            msg = "Statutory regulatory filing or compliance notification under review"
            contradicting.append(msg)

        if news_cnt_72h == 0:
            msg = "No high-impact corporate announcements in past 72h; trading driven by technical flows"
            if signal == "HOLD":
                supporting.append(msg)

        # Realized Volatility Caution
        if realized_vol > 0.28:
            msg = f"Elevated 20-day realized volatility ({realized_vol:.1%}) increases tail risk"
            contradicting.append(msg)

        # Default fallback messages if lists are sparse
        if not supporting:
            if signal == "BUY":
                supporting.append("Calibrated statistical model forecasts positive 5-day drift with favorable odds.")
            elif signal == "SELL":
                supporting.append("Technical posture indicates higher probability of downward consolidation.")
            else:
                supporting.append("Balanced risk/reward; current indicators do not meet high-conviction breakout threshold.")

        if not contradicting:
            contradicting.append("Broader market macroeconomic volatility and unexpected headline developments.")

        return supporting[:5], contradicting[:4]

    def build_news_summary(
        self,
        articles: List[Dict[str, Any]],
        symbol: str,
        sentiment_mean_72h: float,
    ) -> str:
        """Constructs a concise 1-2 sentence market and news narrative for the stock."""
        if not articles:
            return f"No material corporate filings or news disclosures recorded for {symbol} in the past 72 hours. Price action is predominantly driven by technical market structure."

        latest = articles[0]
        headline = latest.get("headline", "")
        event = latest.get("event_category", "GENERAL")
        publisher = latest.get("publisher", "Official Announcement")

        if sentiment_mean_72h > 0.15:
            sentiment_tone = "predominantly positive"
        elif sentiment_mean_72h < -0.15:
            sentiment_tone = "cautious to negative"
        else:
            sentiment_tone = "balanced"

        return f"Recent corporate coverage reflects a {sentiment_tone} tone, highlighted by: '{headline}' ({publisher}, event: {event})."

    def predict_for_instrument(
        self,
        db: Session,
        symbol: str,
        force_refresh: bool = False,
        persist: bool = True,
    ) -> PredictionResponse:
        """
        Runs the full inference pipeline for a given stock symbol:
        1. Fetch instrument and candles.
        2. Verify data quality and freshness gates.
        3. Extract technical indicators and lag-aligned news features.
        4. Predict calibrated probabilities.
        5. Apply deterministic strategy decision rules (BUY/HOLD/SELL/NO_TRADE).
        6. Compute explainability attributions.
        7. Persist to DB and return typed PredictionResponse.
        """
        symbol_upper = symbol.upper()
        inst = db.query(Instrument).filter(Instrument.symbol == symbol_upper).first()
        if not inst:
            raise ValueError(f"Instrument '{symbol_upper}' not found in database.")

        self.load_model(db=db)

        # 1. Fetch candles
        candles = (
            db.query(MarketCandle)
            .filter(MarketCandle.instrument_id == inst.id, MarketCandle.interval == "1d")
            .order_by(MarketCandle.timestamp.asc())
            .all()
        )

        # 2. Check freshness and data quality
        data_quality_status, is_stale, stale_warning = self.assess_staleness_and_quality(candles)

        # 3. Fetch news articles
        news_records = (
            db.query(NewsArticle, NewsSentimentResult)
            .join(NewsCompanyAssociation, NewsCompanyAssociation.article_id == NewsArticle.id)
            .outerjoin(NewsSentimentResult, NewsSentimentResult.article_id == NewsArticle.id)
            .filter(NewsCompanyAssociation.instrument_id == inst.id)
            .order_by(NewsArticle.published_at.desc())
            .limit(30)
            .all()
        )

        formatted_news = []
        for art, sent in news_records:
            formatted_news.append({
                "headline": art.headline,
                "publisher": art.publisher,
                "published_at": art.published_at,
                "first_seen_at": art.first_seen_at or art.published_at,
                "sentiment_score": float(sent.sentiment_score) if sent and sent.sentiment_score is not None else 0.0,
                "event_category": sent.event_category if sent and sent.event_category else "GENERAL",
            })

        # 4. Feature engineering
        if not candles or len(candles) < 20:
            # Insufficient candles fallback
            prob_up = 0.50
            prob_down = 0.50
            expected_ret = 0.00
            ret_interval = [-0.015, 0.015]
            risk_level = "HIGH"
            signal = "NO_TRADE"
            supporting, contradicting = self.generate_explainability_factors(
                pd.Series(), signal, prob_up, stale_warning
            )
            news_summary = self.build_news_summary(formatted_news, symbol_upper, 0.0)
            as_of_time = datetime.utcnow()
        else:
            candle_dicts = [
                {
                    "timestamp": c.timestamp,
                    "open": float(c.open),
                    "high": float(c.high),
                    "low": float(c.low),
                    "close": float(c.close),
                    "volume": float(c.volume),
                }
                for c in candles
            ]
            candles_df = pd.DataFrame(candle_dicts).sort_values("timestamp").reset_index(drop=True)
            tech_df = calculate_technical_features(candles_df)
            full_df = align_news_features_with_candles(tech_df, formatted_news)
            latest_feat = full_df.iloc[-1]

            # Model inference
            feature_cols = self._feature_columns or ALL_FEATURE_COLUMNS
            X_input = []
            for col in feature_cols:
                val = latest_feat.get(col, 0.0)
                X_input.append(0.0 if (pd.isna(val) or np.isinf(val)) else float(val))
            X_arr = np.array(X_input).reshape(1, -1)

            if self._model is not None:
                probs = self._model.predict_proba(X_arr)[0]
                prob_down = round(float(probs[0]), 4)
                prob_up = round(float(probs[1]), 4)
            else:
                # Deterministic heuristic fallback when no artifact is on disk
                rsi = float(latest_feat.get("rsi_14", 50.0))
                dist_ema21 = float(latest_feat.get("dist_ema_21", 0.0))
                prob_up = round(0.50 + (rsi - 50.0) * 0.004 + dist_ema21 * 0.5, 4)
                prob_up = max(0.20, min(0.85, prob_up))
                prob_down = round(1.0 - prob_up, 4)

            # Risk level and expected return
            atr_norm = float(latest_feat.get("atr_14_norm", 0.02))
            realized_vol = float(latest_feat.get("realized_vol_20", 0.16))
            risk_level = self.compute_risk_level(atr_norm, realized_vol)

            sigma_5d = max(atr_norm * np.sqrt(5), 0.02)
            expected_ret = round(float((2.0 * prob_up - 1.0) * sigma_5d), 4)
            ret_interval = [
                round(expected_ret - 0.4 * sigma_5d, 4),
                round(expected_ret + 0.4 * sigma_5d, 4),
            ]

            # Deterministic decision rules
            signal = self.evaluate_strategy_rules(
                probability_up=prob_up,
                expected_return=expected_ret,
                risk_level=risk_level,
                data_quality_status=data_quality_status,
            )

            supporting, contradicting = self.generate_explainability_factors(
                latest_feat, signal, prob_up, stale_warning
            )
            sent_mean_72h = float(latest_feat.get("sentiment_mean_72h", 0.0))
            news_summary = self.build_news_summary(formatted_news, symbol_upper, sent_mean_72h)
            as_of_time = datetime.utcnow()

        # 5. Persist to DB
        if persist:
            existing_pred = (
                db.query(Prediction)
                .filter(Prediction.instrument_id == inst.id)
                .order_by(Prediction.as_of.desc())
                .first()
            )

            if existing_pred:
                existing_pred.as_of = as_of_time
                existing_pred.model_id = self._model_registry_id
                existing_pred.probability_up = prob_up
                existing_pred.probability_down = prob_down
                existing_pred.expected_return = expected_ret
                existing_pred.signal = signal
                existing_pred.risk_level = risk_level
                existing_pred.supporting_factors = supporting
                existing_pred.contradicting_factors = contradicting
                existing_pred.data_quality_status = data_quality_status
                existing_pred.news_summary = news_summary
            else:
                new_pred = Prediction(
                    id=str(uuid.uuid4()),
                    instrument_id=inst.id,
                    model_id=self._model_registry_id,
                    as_of=as_of_time,
                    forecast_horizon="5_trading_sessions",
                    probability_up=prob_up,
                    probability_down=prob_down,
                    expected_return=expected_ret,
                    signal=signal,
                    risk_level=risk_level,
                    supporting_factors=supporting,
                    contradicting_factors=contradicting,
                    data_quality_status=data_quality_status,
                    news_summary=news_summary,
                )
                db.add(new_pred)
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error persisting prediction for {symbol_upper}: {e}")

        is_live = bool(settings.GROWW_ACCESS_TOKEN)

        return PredictionResponse(
            symbol=inst.symbol,
            exchange=inst.exchange,
            as_of=as_of_time,
            forecast_horizon="5_trading_sessions",
            model_version=self._model_version or settings.ACTIVE_MODEL_VERSION,
            probability_up=prob_up,
            probability_down=prob_down,
            expected_return=expected_ret,
            expected_return_interval=ret_interval,
            signal=signal,
            risk_level=risk_level,
            supporting_factors=supporting,
            contradicting_factors=contradicting,
            data_quality_status=data_quality_status,
            news_summary=news_summary,
            limitations=[
                "Walk-forward calibrated probabilistic model (5-day holding horizon).",
                "Deterministic risk thresholds apply capital protection filters.",
                "Not SEBI registered financial advice or guaranteed profit return.",
            ],
            is_demo=not is_live,
        )

    def predict_all(self, db: Session, force_refresh: bool = False) -> List[PredictionResponse]:
        """Runs batch inference across all tracked instruments in the database."""
        instruments = db.query(Instrument).all()
        results: List[PredictionResponse] = []
        for inst in instruments:
            try:
                pred = self.predict_for_instrument(db, inst.symbol, force_refresh=force_refresh, persist=True)
                results.append(pred)
            except Exception as e:
                logger.error(f"Failed generating prediction for {inst.symbol}: {e}")
        return results


# Global singleton instance
prediction_service = PredictionService()

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.session import Base


class ModelRegistry(Base):
    __tablename__ = "models_registry"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_version = Column(String(64), unique=True, nullable=False, index=True)
    algorithm = Column(String(64), nullable=False)  # 'LIGHTGBM', 'LOGISTIC_REGRESSION', 'BASELINE'
    features_schema_version = Column(String(32), nullable=False)
    training_start_date = Column(DateTime, nullable=False)
    training_end_date = Column(DateTime, nullable=False)
    artifact_path = Column(Text, nullable=False)
    calibration_method = Column(String(32), default="ISOTONIC", nullable=False)
    roc_auc = Column(Numeric(6, 4), nullable=True)
    brier_score = Column(Numeric(6, 4), nullable=True)
    log_loss = Column(Numeric(6, 4), nullable=True)
    is_active = Column(Numeric(1, 0), default=1, nullable=False)  # 1 for active
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    predictions = relationship("Prediction", back_populates="model")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    instrument_id = Column(String(36), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    model_id = Column(String(36), ForeignKey("models_registry.id"), nullable=True, index=True)
    as_of = Column(DateTime, nullable=False, index=True)
    forecast_horizon = Column(String(32), default="5_trading_sessions", nullable=False)
    probability_up = Column(Numeric(5, 4), nullable=True)
    probability_down = Column(Numeric(5, 4), nullable=True)
    expected_return = Column(Numeric(8, 4), nullable=True)
    signal = Column(String(16), nullable=False, index=True)  # 'BUY', 'HOLD', 'SELL', 'NO_TRADE'
    risk_level = Column(String(16), nullable=False)          # 'LOW', 'MEDIUM', 'HIGH', 'EXTREME'
    supporting_factors = Column(JSON, nullable=False, default=list)
    contradicting_factors = Column(JSON, nullable=False, default=list)
    data_quality_status = Column(String(32), default="VERIFIED_FRESH", nullable=False)
    news_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    instrument = relationship("Instrument", back_populates="predictions")
    model = relationship("ModelRegistry", back_populates="predictions")

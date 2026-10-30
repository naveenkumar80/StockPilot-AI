from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class PredictionResponse(BaseModel):
    symbol: str
    exchange: str
    as_of: datetime
    forecast_horizon: str
    model_version: str
    probability_up: Optional[float] = None
    probability_down: Optional[float] = None
    expected_return: Optional[float] = None
    expected_return_interval: Optional[List[float]] = None
    signal: str  # 'BUY', 'HOLD', 'SELL', 'NO_TRADE'
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH', 'EXTREME'
    supporting_factors: List[str]
    contradicting_factors: List[str]
    data_quality_status: str
    news_summary: Optional[str] = None
    limitations: List[str] = []
    is_demo: bool = False


class ModelMetricsResponse(BaseModel):
    model_version: str
    algorithm: str
    features_schema_version: str
    training_period: str
    roc_auc: float
    brier_score: float
    log_loss: float
    precision_buy: float
    recall_buy: float
    walk_forward_sharpe: float
    max_drawdown_pct: float
    calibration_method: str
    price_only_vs_news_comparison: dict

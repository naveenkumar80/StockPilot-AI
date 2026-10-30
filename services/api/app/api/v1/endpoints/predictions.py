from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.prediction import Prediction
from app.models.instrument import Instrument
from app.schemas.prediction import PredictionResponse
from app.services.prediction_service import prediction_service
from app.core.config import settings

router = APIRouter()


@router.get("", response_model=List[PredictionResponse])
def list_predictions(
    signal: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List the latest predictions across tracked instruments,
    with optional filtering by signal (BUY, HOLD, SELL, NO_TRADE).
    """
    q = (
        db.query(Prediction, Instrument.symbol, Instrument.exchange)
        .join(Instrument, Prediction.instrument_id == Instrument.id)
        .order_by(Prediction.as_of.desc())
    )
    if signal:
        q = q.filter(Prediction.signal == signal.upper())

    results = q.limit(limit).all()

    # If DB has no predictions yet, generate batch inference
    if not results:
        preds = prediction_service.predict_all(db, force_refresh=False)
        if signal:
            preds = [p for p in preds if p.signal == signal.upper()]
        return preds[:limit]

    is_live = bool(settings.GROWW_ACCESS_TOKEN)

    return [
        PredictionResponse(
            symbol=sym,
            exchange=exch,
            as_of=pred.as_of,
            forecast_horizon=pred.forecast_horizon,
            model_version=settings.ACTIVE_MODEL_VERSION,
            probability_up=float(pred.probability_up) if pred.probability_up is not None else None,
            probability_down=float(pred.probability_down) if pred.probability_down is not None else None,
            expected_return=float(pred.expected_return) if pred.expected_return is not None else None,
            expected_return_interval=[
                round(float(pred.expected_return) - 0.015, 4),
                round(float(pred.expected_return) + 0.025, 4),
            ] if pred.expected_return is not None else None,
            signal=pred.signal,
            risk_level=pred.risk_level,
            supporting_factors=pred.supporting_factors or [],
            contradicting_factors=pred.contradicting_factors or [],
            data_quality_status=pred.data_quality_status,
            news_summary=pred.news_summary,
            limitations=[
                "Walk-forward validated probabilistic classifier.",
                "Not financial or investment advice."
            ],
            is_demo=not is_live,
        )
        for pred, sym, exch in results
    ]


@router.get("/{symbol}", response_model=PredictionResponse)
def get_symbol_prediction(
    symbol: str,
    force_refresh: bool = False,
    db: Session = Depends(get_db),
):
    """
    Fetch the latest calibrated prediction and factor attribution for a specific stock symbol.
    Generates real-time inference on demand if no prior prediction exists or force_refresh is requested.
    """
    sym = symbol.upper()
    inst = db.query(Instrument).filter(Instrument.symbol == sym).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{sym}' not found in instrument universe",
        )

    if force_refresh:
        return prediction_service.predict_for_instrument(db, sym, force_refresh=True)

    # Check for existing recent prediction
    pred = (
        db.query(Prediction)
        .filter(Prediction.instrument_id == inst.id)
        .order_by(Prediction.as_of.desc())
        .first()
    )

    if pred:
        is_live = bool(settings.GROWW_ACCESS_TOKEN)
        return PredictionResponse(
            symbol=inst.symbol,
            exchange=inst.exchange,
            as_of=pred.as_of,
            forecast_horizon=pred.forecast_horizon,
            model_version=settings.ACTIVE_MODEL_VERSION,
            probability_up=float(pred.probability_up) if pred.probability_up is not None else None,
            probability_down=float(pred.probability_down) if pred.probability_down is not None else None,
            expected_return=float(pred.expected_return) if pred.expected_return is not None else None,
            expected_return_interval=[
                round(float(pred.expected_return) - 0.015, 4),
                round(float(pred.expected_return) + 0.025, 4),
            ] if pred.expected_return is not None else None,
            signal=pred.signal,
            risk_level=pred.risk_level,
            supporting_factors=pred.supporting_factors or [],
            contradicting_factors=pred.contradicting_factors or [],
            data_quality_status=pred.data_quality_status,
            news_summary=pred.news_summary,
            limitations=[
                "Walk-forward calibrated probabilistic model (5-day holding horizon).",
                "Deterministic risk thresholds apply capital protection filters.",
                "Not SEBI registered financial advice or guaranteed profit return.",
            ],
            is_demo=not is_live,
        )

    # Otherwise generate real-time prediction
    return prediction_service.predict_for_instrument(db, sym, force_refresh=False)


@router.post("/{symbol}/refresh", response_model=PredictionResponse)
def refresh_symbol_prediction(
    symbol: str,
    db: Session = Depends(get_db),
):
    """
    Force executes real-time inference with latest market data and news features,
    persisting the updated prediction to the database.
    """
    sym = symbol.upper()
    inst = db.query(Instrument).filter(Instrument.symbol == sym).first()
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{sym}' not found in instrument universe",
        )

    return prediction_service.predict_for_instrument(db, sym, force_refresh=True, persist=True)


@router.post("/batch-refresh", response_model=List[PredictionResponse])
def batch_refresh_predictions(
    db: Session = Depends(get_db),
):
    """
    Batch recalculate predictions for all tracked instruments.
    """
    return prediction_service.predict_all(db, force_refresh=True)

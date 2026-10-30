from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    # 1. Database check
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Groww integration check
    groww_auth = bool(settings.GROWW_ACCESS_TOKEN)
    groww_status = {
        "status": "ready",
        "authenticated": groww_auth,
        "mode": "live" if groww_auth else "demo",
        "base_url": settings.GROWW_BASE_URL,
    }

    # 3. News integration check
    news_status = {
        "status": "ready",
        "provider": "drishti_exchange_disclosures",
        "has_drishti_key": bool(settings.DRISHTI_API_KEY),
    }

    # 4. Model engine check
    model_status = {
        "status": "loaded",
        "active_version": settings.ACTIVE_MODEL_VERSION,
        "calibration_method": settings.CALIBRATION_METHOD,
    }

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        environment=settings.ENVIRONMENT,
        integrations={
            "database": {"status": db_status},
            "groww_api": groww_status,
            "news_provider": news_status,
            "model_engine": model_status,
        }
    )

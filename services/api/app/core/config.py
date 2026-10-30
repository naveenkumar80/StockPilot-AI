from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PROJECT_NAME: str = "StockPilot AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key-stockpilot-ai-2026"

    # Database
    DATABASE_URL: str = "sqlite:///./stockpilot.db"
    DATABASE_ECHO: bool = False

    # External APIs
    GROWW_API_KEY: Optional[str] = None
    GROWW_ACCESS_TOKEN: Optional[str] = None
    GROWW_BASE_URL: str = "https://api.groww.in/v1"
    GROWW_TIMEOUT_SECONDS: int = 15

    # ICICI Direct Breeze API (Backup Market Data Provider)
    ICICI_BREEZE_API_KEY: Optional[str] = None
    ICICI_BREEZE_API_SECRET: Optional[str] = None
    ICICI_BREEZE_SESSION_TOKEN: Optional[str] = None

    DRISHTI_API_KEY: Optional[str] = None
    NEWS_FETCH_INTERVAL_MINUTES: int = 30

    # ML & Inference
    MODEL_ARTIFACTS_DIR: str = "./services/ml/artifacts"
    ACTIVE_MODEL_VERSION: str = "v1.0.0-lgbm"
    CALIBRATION_METHOD: str = "ISOTONIC"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]


settings = Settings()

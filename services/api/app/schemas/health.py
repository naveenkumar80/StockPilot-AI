from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel


class IntegrationStatus(BaseModel):
    status: str
    authenticated: Optional[bool] = None
    mode: Optional[str] = None
    latency_ms: Optional[float] = None
    provider: Optional[str] = None
    last_ingest: Optional[datetime] = None
    active_version: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    environment: str
    integrations: Dict[str, Any]

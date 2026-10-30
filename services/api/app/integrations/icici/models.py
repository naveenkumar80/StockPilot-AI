from typing import Optional
from pydantic import BaseModel


class BreezeStatusResponse(BaseModel):
    is_configured: bool
    is_session_active: bool
    api_key_configured: bool
    api_secret_configured: bool
    session_token_configured: bool
    login_url: Optional[str] = None
    last_error: Optional[str] = None


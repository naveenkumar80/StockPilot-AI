class GrowwError(Exception):
    """Base exception for all Groww integration errors."""
    pass


class GrowwAuthenticationError(GrowwError):
    """Raised when authentication fails (HTTP 401 or invalid access token)."""
    pass


class GrowwRateLimitError(GrowwError):
    """Raised when API rate limit is exceeded (HTTP 429)."""
    def __init__(self, message: str, retry_after: int = 5):
        super().__init__(message)
        self.retry_after = retry_after


class GrowwNetworkError(GrowwError):
    """Raised when connection timeouts or network errors occur."""
    pass


class GrowwDataError(GrowwError):
    """Raised when response payload is malformed or invalid."""
    pass


class CandleValidationError(GrowwError):
    """Raised when candle data fails financial integrity validation."""
    def __init__(self, message: str, violations: list = None):
        super().__init__(message)
        self.violations = violations or []

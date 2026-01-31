"""Custom exceptions for the FMP client."""


class FMPError(Exception):
    """Base exception for all FMP client errors."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FMPAPIError(FMPError):
    """Error returned by the FMP API (non-2xx response)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response_body: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class FMPAuthenticationError(FMPAPIError):
    """API key is invalid or missing (HTTP 401/403)."""


class FMPRateLimitError(FMPAPIError):
    """Rate limit exceeded (HTTP 429)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 429,
        response_body: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(message, status_code=status_code, response_body=response_body)


class FMPNotFoundError(FMPAPIError):
    """Requested resource not found (HTTP 404)."""


class FMPConnectionError(FMPError):
    """Network-level connection error."""


class FMPTimeoutError(FMPError):
    """Request timed out."""

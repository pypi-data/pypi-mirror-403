"""
CONXA SDK Exceptions

Custom exceptions for handling various error scenarios in the SDK.
Aligned with backend error response shape:
  { "status": "error", "message": "<user-facing>", "code": "<optional>", "errors": "<optional>" }
"""


def _message_from_response(response_data: dict) -> str:
    """Extract user-facing message from backend error response."""
    if not response_data:
        return "An error occurred"
    # Backend uses "message" in error_response_body; FastAPI may use "detail" (str or list)
    msg = response_data.get("message")
    if msg:
        return msg
    detail = response_data.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict):
            return first.get("msg") or first.get("message") or "Validation error"
        return str(first)
    return "An error occurred"


class CONXAError(Exception):
    """Base exception for all CONXA SDK errors"""

    def __init__(self, message: str, status_code: int = None, response: dict = None, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(CONXAError):
    """Raised when API key is invalid or missing"""

    def __init__(self, message: str = "Invalid or missing API key", response: dict = None):
        super().__init__(
            message,
            status_code=401,
            response=response or {},
            error_code=(response or {}).get("code"),
        )


class InsufficientBalanceError(CONXAError):
    """Raised when user doesn't have enough tokens (402)"""

    def __init__(
        self, message: str = "Insufficient balance", current_balance: int = None, response: dict = None
    ):
        self.current_balance = current_balance
        super().__init__(
            message,
            status_code=402,
            response=response or {},
            error_code=(response or {}).get("code"),
        )


class SessionExpiredError(CONXAError):
    """Raised when the provider session has expired"""

    def __init__(self, message: str = "Session expired or invalid", response: dict = None):
        super().__init__(
            message,
            status_code=401,
            response=response or {},
            error_code=(response or {}).get("code"),
        )


class ConnectionTimeoutError(CONXAError):
    """Raised when waiting for user connection times out"""

    def __init__(self, message: str = "Connection timeout - user did not connect"):
        super().__init__(message)


class SessionNotFoundError(CONXAError):
    """Raised when no active session is found for the user"""

    def __init__(self, message: str = "No active session found", response: dict = None):
        super().__init__(
            message,
            status_code=404,
            response=response or {},
            error_code=(response or {}).get("code"),
        )


class ProviderNotFoundError(CONXAError):
    """Raised when the provider is not found"""

    def __init__(self, message: str = "Provider not found", response: dict = None):
        super().__init__(
            message,
            status_code=404,
            response=response or {},
            error_code=(response or {}).get("code"),
        )


class ForbiddenError(CONXAError):
    """Raised when request is forbidden (403), e.g. spending limit exceeded or NO_CHARGE_PERMISSION"""

    def __init__(self, message: str = "Forbidden", response: dict = None):
        super().__init__(
            message,
            status_code=403,
            response=response or {},
            error_code=(response or {}).get("code"),
        )


class IdempotencyConflictError(CONXAError):
    """Raised when charge idempotency key is in progress (409)"""

    def __init__(self, message: str = "Idempotency key in progress", response: dict = None):
        super().__init__(
            message,
            status_code=409,
            response=response or {},
            error_code=(response or {}).get("code"),
        )


class RateLimitError(CONXAError):
    """Raised when API rate limit is exceeded"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, response: dict = None):
        self.retry_after = retry_after
        super().__init__(
            message,
            status_code=429,
            response=response or {},
            error_code=(response or {}).get("code"),
        )


class APIError(CONXAError):
    """Raised for general API errors"""

    def __init__(
        self, message: str = "API error occurred", status_code: int = 500, response: dict = None
    ):
        error_code = (response or {}).get("code")
        super().__init__(message, status_code=status_code, response=response or {}, error_code=error_code)


class ValidationError(CONXAError):
    """Raised when request validation fails (422)"""

    def __init__(self, message: str = "Validation error", errors: list = None, response: dict = None):
        self.errors = errors if errors is not None else ((response or {}).get("errors") or [])
        super().__init__(
            message,
            status_code=422,
            response=response or {},
            error_code=(response or {}).get("code"),
        )

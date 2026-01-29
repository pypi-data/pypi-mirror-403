"""
CONXA SDK Exceptions

Custom exceptions for handling various error scenarios in the SDK.
"""


class CONXAError(Exception):
    """Base exception for all CONXA SDK errors"""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(CONXAError):
    """Raised when API key is invalid or missing"""

    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, status_code=401)


class InsufficientBalanceError(CONXAError):
    """Raised when user doesn't have enough tokens"""

    def __init__(
        self, message: str = "Insufficient balance", current_balance: int = None
    ):
        self.current_balance = current_balance
        super().__init__(message, status_code=402)


class SessionExpiredError(CONXAError):
    """Raised when the provider session has expired"""

    def __init__(self, message: str = "Session expired or invalid"):
        super().__init__(message, status_code=401)


class ConnectionTimeoutError(CONXAError):
    """Raised when waiting for user connection times out"""

    def __init__(self, message: str = "Connection timeout - user did not connect"):
        super().__init__(message)


class SessionNotFoundError(CONXAError):
    """Raised when no active session is found for the user"""

    def __init__(self, message: str = "No active session found"):
        super().__init__(message, status_code=404)


class ProviderNotFoundError(CONXAError):
    """Raised when the provider is not found"""

    def __init__(self, message: str = "Provider not found"):
        super().__init__(message, status_code=404)


class RateLimitError(CONXAError):
    """Raised when API rate limit is exceeded"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class APIError(CONXAError):
    """Raised for general API errors"""

    def __init__(
        self, message: str = "API error occurred", status_code: int = 500, response: dict = None
    ):
        super().__init__(message, status_code=status_code, response=response)


class ValidationError(CONXAError):
    """Raised when request validation fails"""

    def __init__(self, message: str = "Validation error", errors: list = None):
        self.errors = errors or []
        super().__init__(message, status_code=422)

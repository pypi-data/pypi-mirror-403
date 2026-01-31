"""
CONXA SDK - Python client library for AI providers to integrate CONXA Wallet

This SDK enables AI providers (ChatGPT, Claude, etc.) to:
1. Generate QR codes for users to connect their CONXA wallet
2. Poll for user connection status
3. Charge users for AI usage (tokens)
4. Check user balance

Example:
    from conxa import CONXAClient
    
    client = CONXAClient(api_key="pk_live_xxx")
    
    # Generate QR for user to scan
    qr = client.create_payment_qr(provider_username="user@example.com")
    
    # Wait for user to connect
    session = client.wait_for_connection(provider_username="user@example.com")
    
    # Charge for AI usage
    result = client.charge(
        session_token=session.session_token,
        idempotency_key="req_abc123",  # unique per logical charge (e.g. request ID)
        model_name="gpt-4",
        input_tokens=1000,
        output_tokens=500
    )
"""

from .client import CONXAClient
from .models import (
    QRCodeData,
    SessionStatus,
    ChargeResult,
    WalletBalance,
    ConnectionStatus,
)
from .exceptions import (
    CONXAError,
    AuthenticationError,
    InsufficientBalanceError,
    SessionExpiredError,
    ConnectionTimeoutError,
    SessionNotFoundError,
    ProviderNotFoundError,
    ForbiddenError,
    IdempotencyConflictError,
    RateLimitError,
    APIError,
    ValidationError,
)

__version__ = "1.4.0"
__author__ = "CONXA Team"
__all__ = [
    "CONXAClient",
    "QRCodeData",
    "SessionStatus",
    "ChargeResult",
    "WalletBalance",
    "ConnectionStatus",
    "CONXAError",
    "AuthenticationError",
    "InsufficientBalanceError",
    "SessionExpiredError",
    "ConnectionTimeoutError",
    "SessionNotFoundError",
    "ProviderNotFoundError",
    "ForbiddenError",
    "IdempotencyConflictError",
    "RateLimitError",
    "APIError",
    "ValidationError",
]

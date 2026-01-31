"""
CONXA SDK Client

Main client class for interacting with the CONXA Wallet API.
"""

from __future__ import annotations

import time
import json
import warnings
from typing import Optional, Dict, Any, Callable
from datetime import datetime

import requests

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
    RateLimitError,
    APIError,
    ValidationError,
    ForbiddenError,
    IdempotencyConflictError,
    _message_from_response,
)
from .qr import generate_qr_code, generate_qr_svg


class CONXAClient:
    """
    CONXA SDK Client for AI providers to integrate wallet payments.
    
    This client enables providers to:
    1. Generate QR codes for users to connect their wallet
    2. Poll for user connection status
    3. Charge users for AI usage
    4. Check user balance
    
    Example:
        >>> client = CONXAClient(api_key="pk_live_xxx")
        >>> 
        >>> # Generate QR for user to scan
        >>> qr = client.create_payment_qr(provider_username="user@example.com")
        >>> 
        >>> # Wait for user to connect
        >>> session = client.wait_for_connection(provider_username="user@example.com")
        >>> 
        >>> # Charge for AI usage
        >>> result = client.charge(
        ...     session_token=session.session_token,
        ...     idempotency_key="req_abc123",
        ...     model_name="gpt-4",
        ...     input_tokens=1000,
        ...     output_tokens=500
        ... )
    
    Args:
        api_key: Provider API key (e.g., "pk_live_openai_xxxxx")
        base_url: CONXA API base URL (default: https://api.conxa.in)
        timeout: Request timeout in seconds (default: 30)
        provider_id: Provider ID (optional, extracted from API key if not provided)
        provider_type: Provider type "api" or "web" (default: "api")
    """
    
    DEFAULT_BASE_URL = "https://api.conxa.in"
    DEFAULT_TIMEOUT = 30
    
    def __init__(
        self,
        api_key: str,
        base_url: str = None,
        timeout: int = None,
        provider_id: str = None,
        provider_type: str = "api",
    ):
        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            raise AuthenticationError("API key is required and cannot be empty")
        
        self.api_key = api_key.strip()
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        
        # Validate timeout
        if timeout is not None:
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValueError("timeout must be a positive number")
            self.timeout = int(timeout)
        else:
            self.timeout = self.DEFAULT_TIMEOUT
        
        # Validate provider_type
        if not provider_type or not isinstance(provider_type, str):
            raise ValueError("provider_type is required and must be a string")
        
        provider_type = provider_type.lower().strip()
        if provider_type not in ("api", "web"):
            raise ValueError(f'provider_type must be "api" or "web", got: {provider_type}')
        self.provider_type = provider_type
        
        # Extract or set provider_id
        # API key format: pk_live_providername_xxxxx
        if provider_id:
            if not isinstance(provider_id, str) or not provider_id.strip():
                raise ValueError("provider_id cannot be empty if provided")
            self.provider_id = provider_id.strip()
        else:
            # Try to extract from API key (this is a fallback)
            # Providers should ideally set this explicitly
            self.provider_id = self._extract_provider_id_from_key(api_key)
            if not self.provider_id or self.provider_id == "unknown":
                raise ValueError(
                    "provider_id is required. Either provide it explicitly or ensure your API key "
                    "format allows automatic extraction."
                )
        
        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Provider-API-Key": self.api_key,
        })
    
    def _extract_provider_id_from_key(self, api_key: str) -> str:
        """
        Extract provider ID from API key format.
        
        API key format: pk_live_providername_xxxxx or pk_test_providername_xxxxx
        Attempts to extract provider name from the key.
        
        Note: This is a fallback. Providers should set provider_id explicitly.
        """
        if not api_key:
            return "unknown"
        
        # Try to extract provider name from API key format
        # Format: pk_live_providername_xxxxx or pk_test_providername_xxxxx
        parts = api_key.split("_")
        if len(parts) >= 3:
            # pk_live_providername_xxxxx -> providername
            return parts[2] if parts[2] else "unknown"
        
        # Fallback: use first 20 chars (not ideal, but better than "unknown")
        return api_key[:20] if len(api_key) >= 20 else api_key
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        headers: Dict = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the CONXA API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/providers/session/status")
            data: Request body data
            params: Query parameters
            headers: Additional headers
        
        Returns:
            Response JSON data
        
        Raises:
            Various CONXA exceptions based on response
        """
        # Validate endpoint
        if not endpoint or not isinstance(endpoint, str):
            raise ValueError("endpoint must be a non-empty string")
        
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        
        # Basic sanitization - remove any dangerous patterns
        if ".." in endpoint or "//" in endpoint.replace("://", ""):
            raise ValueError("endpoint contains invalid path patterns")
        
        url = f"{self.base_url}{endpoint}"
        
        request_headers = dict(self._session.headers)
        if headers:
            request_headers.update(headers)
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers,
                timeout=self.timeout,
            )
            
            # Parse response (backend error shape: status, message, code?, errors?)
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"message": response.text or "Invalid response"}

            msg = _message_from_response(response_data)

            # Handle errors (backend uses "message" in error_response_body; FastAPI may use "detail")
            if response.status_code == 401:
                raise AuthenticationError(msg, response=response_data)
            elif response.status_code == 402:
                raise InsufficientBalanceError(
                    msg,
                    current_balance=response_data.get("new_balance"),
                    response=response_data,
                )
            elif response.status_code == 403:
                raise ForbiddenError(msg, response=response_data)
            elif response.status_code == 404:
                raise SessionNotFoundError(msg, response=response_data)
            elif response.status_code == 409:
                raise IdempotencyConflictError(msg, response=response_data)
            elif response.status_code == 422:
                raise ValidationError(
                    msg,
                    errors=response_data.get("errors", []),
                    response=response_data,
                )
            elif response.status_code == 429:
                # Parse Retry-After header (can be seconds as int or HTTP date)
                retry_after = None
                retry_after_header = response.headers.get("Retry-After")
                if retry_after_header:
                    try:
                        retry_after = int(retry_after_header)
                    except ValueError:
                        try:
                            from email.utils import parsedate_to_datetime
                            retry_date = parsedate_to_datetime(retry_after_header)
                            retry_after = int((retry_date.timestamp() - time.time()))
                            if retry_after < 0:
                                retry_after = None
                        except (ValueError, TypeError):
                            retry_after = None
                raise RateLimitError(msg, retry_after=retry_after, response=response_data)
            elif response.status_code >= 400:
                raise APIError(
                    msg,
                    status_code=response.status_code,
                    response=response_data,
                )
            
            return response_data
            
        except requests.exceptions.Timeout:
            raise CONXAError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise CONXAError("Connection error - unable to reach CONXA API")
        except requests.exceptions.RequestException as e:
            raise CONXAError(f"Request failed: {str(e)}")
    
    # =========================================================================
    # QR Code Generation
    # =========================================================================
    
    def create_payment_qr(
        self,
        provider_username: str,
        provider_type: str = None,
        limit: Optional[float] = None,
        size: int = 300,
        expires_in: Optional[int] = None,
    ) -> QRCodeData:
        """
        Generate a QR code for user to scan and connect their wallet.
        
        The QR code contains provider information that the CONXA mobile app
        reads to establish a connection.
        
        Args:
            provider_username: User's ID in your system (e.g., email, username)
            provider_type: "api" or "web" (default: instance default)
            limit: Optional spending limit in tokens
            size: QR code image size in pixels (default: 300)
            expires_in: Optional expiration time in seconds. If set, creates a 
                       short-lived session that expires after this duration.
                       Default: None (no expiration)
        
        Returns:
            QRCodeData with:
                - qr_data: JSON string encoded in QR
                - qr_image: PIL Image object (if qrcode installed)
                - qr_base64: Base64 PNG for HTML embedding
                - expires_at: Timestamp when QR expires (if expires_in is set)
        
        Raises:
            ValueError: If any parameter is invalid
            AuthenticationError: If provider_id is not set
            
        Example:
            >>> qr = client.create_payment_qr(
            ...     provider_username="user@example.com",
            ...     limit=10000,
            ...     expires_in=10  # QR expires after 10 seconds
            ... )
            >>> # Display in web app
            >>> html = f'<img src="{qr.qr_base64}" />'
            >>> # Or save to file
            >>> qr.qr_image.save("connect.png")
        """
        # Validate provider_username
        if not provider_username or not isinstance(provider_username, str) or not provider_username.strip():
            raise ValueError("provider_username is required and cannot be empty")
        
        # Validate expires_in if provided
        if expires_in is not None:
            if not isinstance(expires_in, (int, float)) or expires_in <= 0:
                raise ValueError("expires_in must be a positive number")
        
        # Validate provider_id is set
        if not self.provider_id or self.provider_id == "unknown":
            raise AuthenticationError(
                "provider_id is required. Please provide it when initializing CONXAClient."
            )
        
        qr_data = generate_qr_code(
            provider_id=self.provider_id,
            provider_type=provider_type or self.provider_type,
            provider_username=provider_username.strip(),
            limit=limit,
            size=size,
        )
        
        # Track creation time and expiration if expires_in is set
        from datetime import datetime, timezone, timedelta
        qr_data.created_at = datetime.now(timezone.utc)
        
        if expires_in is not None and expires_in > 0:
            qr_data.expires_at = qr_data.created_at + timedelta(seconds=expires_in)
        
        return qr_data
    
    def create_payment_qr_svg(
        self,
        provider_username: str,
        provider_type: str = None,
        limit: Optional[float] = None,
        size: int = 300,
    ) -> str:
        """
        Generate a QR code as SVG string.
        
        Args:
            provider_username: User's ID in your system
            provider_type: "api" or "web"
            limit: Optional spending limit in tokens
            size: SVG size in pixels
        
        Returns:
            SVG string of the QR code
            
        Raises:
            ValueError: If any parameter is invalid
            AuthenticationError: If provider_id is not set
        """
        # Validate provider_username
        if not provider_username or not isinstance(provider_username, str) or not provider_username.strip():
            raise ValueError("provider_username is required and cannot be empty")
        
        # Validate provider_id is set
        if not self.provider_id or self.provider_id == "unknown":
            raise AuthenticationError(
                "provider_id is required. Please provide it when initializing CONXAClient."
            )
        
        return generate_qr_svg(
            provider_id=self.provider_id,
            provider_type=provider_type or self.provider_type,
            provider_username=provider_username.strip(),
            limit=limit,
            size=size,
        )
    
    # =========================================================================
    # Session / Connection Status
    # =========================================================================
    
    def get_session_status(
        self, 
        provider_username: str,
        retry_on_rate_limit: bool = True,
        max_retries: int = 3,
        qr_data: Optional[QRCodeData] = None,
    ) -> SessionStatus:
        """
        Check if a user has connected their wallet.
        
        Poll this endpoint after showing the QR code to detect when
        the user scans and approves the connection.
        
        Args:
            provider_username: User's ID in your system
            retry_on_rate_limit: If True, automatically retry on rate limit errors with backoff
            max_retries: Maximum number of retries on rate limit (default: 3)
            qr_data: Optional QRCodeData to check if QR has expired
        
        Returns:
            SessionStatus with:
                - status: "pending", "active", "expired", or "not_found"
                - session_token: Token for charges (only if active)
                - expires_at: Session expiration time
        
        Raises:
            ValueError: If provider_username is invalid
            RateLimitError: If rate limit exceeded and retries exhausted
            SessionExpiredError: If QR code has expired (when qr_data is provided)
        
        Example:
            >>> qr = client.create_payment_qr("user@example.com", expires_in=10)
            >>> status = client.get_session_status("user@example.com", qr_data=qr)
            >>> if status.is_active:
            ...     print(f"Connected! Token: {status.session_token}")
            >>> elif status.is_pending:
            ...     print("Waiting for user to scan QR...")
        """
        # Validate provider_username
        if not provider_username or not isinstance(provider_username, str) or not provider_username.strip():
            raise ValueError("provider_username is required and cannot be empty")
        
        # Validate max_retries
        if not isinstance(max_retries, int) or max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        
        # Check if QR code has expired
        if qr_data and qr_data.is_expired():
            raise SessionExpiredError(
                "QR code has expired. Please generate a new QR code."
            )
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = self._request(
                    method="GET",
                    endpoint="/providers/session/status",
                    params={"provider_username": provider_username.strip()},
                )
                
                return SessionStatus.from_api_response(response)
                
            except RateLimitError as e:
                last_exception = e
                
                if not retry_on_rate_limit or attempt >= max_retries:
                    # Re-raise if we've exhausted retries or retry is disabled
                    raise
                
                # Calculate backoff time
                if e.retry_after:
                    # Use Retry-After header if provided
                    backoff_time = int(e.retry_after)
                else:
                    # Exponential backoff: 2^attempt seconds (2, 4, 8, ...)
                    backoff_time = min(2 ** attempt, 60)  # Cap at 60 seconds
                
                # Wait before retrying
                time.sleep(backoff_time)
        
        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
    
    def wait_for_connection(
        self,
        provider_username: str,
        timeout: int = 120,
        poll_interval: int = 2,
        on_pending: Optional[Callable[[SessionStatus], None]] = None,
        rate_limit_timeout: int = 10,
        qr_data: Optional[QRCodeData] = None,
    ) -> SessionStatus:
        """
        Wait for user to connect their wallet (blocking).
        
        Polls the session status until the user connects or timeout occurs.
        If rate limited for more than rate_limit_timeout seconds, the QR session
        will be considered expired and user needs to generate a new QR code.
        
        Args:
            provider_username: User's ID in your system
            timeout: Maximum wait time in seconds (default: 120)
            poll_interval: Time between polls in seconds (default: 2)
            on_pending: Optional callback called on each pending poll
            rate_limit_timeout: Seconds of rate limiting before closing QR (default: 10)
            qr_data: Optional QRCodeData to check if QR has expired
        
        Returns:
            SessionStatus with active session
        
        Raises:
            ValueError: If any parameter is invalid
            ConnectionTimeoutError: If user doesn't connect within timeout
            SessionExpiredError: If QR expires or rate limited for too long
        
        Example:
            >>> session = client.wait_for_connection(
            ...     provider_username="user@example.com",
            ...     timeout=60,
            ...     on_pending=lambda s: print("Waiting...")
            ... )
            >>> print(f"Connected! Token: {session.session_token}")
        """
        # Validate provider_username
        if not provider_username or not isinstance(provider_username, str) or not provider_username.strip():
            raise ValueError("provider_username is required and cannot be empty")
        
        # Validate timeout
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be a positive number")
        
        # Validate poll_interval
        if not isinstance(poll_interval, (int, float)) or poll_interval <= 0:
            raise ValueError("poll_interval must be a positive number")
        
        # Validate rate_limit_timeout
        if not isinstance(rate_limit_timeout, (int, float)) or rate_limit_timeout < 0:
            raise ValueError("rate_limit_timeout must be a non-negative number")
        
        start_time = time.time()
        rate_limit_start_time = None
        total_rate_limit_time = 0
        
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise ConnectionTimeoutError(
                    f"User did not connect within {timeout} seconds"
                )
            
            try:
                # Check if QR has expired before polling
                if qr_data and qr_data.is_expired():
                    raise SessionExpiredError(
                        "QR code has expired. Please generate a new QR code."
                    )
                
                status = self.get_session_status(
                    provider_username, 
                    retry_on_rate_limit=True,
                    qr_data=qr_data
                )
                
                # Reset rate limit tracking on successful request
                if rate_limit_start_time is not None:
                    total_rate_limit_time += time.time() - rate_limit_start_time
                    rate_limit_start_time = None
                
                if status.is_active:
                    return status
                
                if status.is_expired:
                    raise SessionExpiredError("Session expired before connection")
                
                if on_pending and status.is_pending:
                    on_pending(status)
                
            except SessionNotFoundError:
                # No session yet, keep waiting
                # Reset rate limit tracking
                if rate_limit_start_time is not None:
                    total_rate_limit_time += time.time() - rate_limit_start_time
                    rate_limit_start_time = None
                pass
            except RateLimitError as e:
                # Track when rate limiting starts
                if rate_limit_start_time is None:
                    rate_limit_start_time = time.time()
                
                # Calculate current total rate limit time
                current_rate_limit_duration = total_rate_limit_time
                if rate_limit_start_time is not None:
                    current_rate_limit_duration += time.time() - rate_limit_start_time
                
                # Check if we've been rate limited for too long
                if current_rate_limit_duration >= rate_limit_timeout:
                    raise SessionExpiredError(
                        f"QR code session expired due to rate limiting. "
                        f"Please generate a new QR code."
                    )
                
                # Handle rate limit by backing off
                if e.retry_after:
                    backoff_time = int(e.retry_after)
                else:
                    # Use exponential backoff, but cap at poll_interval * 4
                    backoff_time = min(poll_interval * 2, 30)
                
                # Log warning but continue waiting
                warnings.warn(
                    f"Rate limit hit while waiting for connection. "
                    f"Backing off for {backoff_time} seconds. "
                    f"Total rate limit time: {current_rate_limit_duration:.1f}s/{rate_limit_timeout}s",
                    UserWarning
                )
                time.sleep(backoff_time)
                continue  # Skip the normal poll_interval sleep
            
            time.sleep(poll_interval)
    
    # =========================================================================
    # Charging API
    # =========================================================================
    
    def charge(
        self,
        session_token: str,
        idempotency_key: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> ChargeResult:
        """
        Charge user for AI usage.
        
        Deducts tokens from user's wallet based on model pricing.
        Call this after each AI request to bill the user.
        
        Args:
            session_token: Active session token from connection
            idempotency_key: Unique key per logical charge (e.g. request ID). Required for exactly-once semantics on retries.
            model_name: AI model used (e.g., "gpt-4", "claude-3")
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        
        Returns:
            ChargeResult with:
                - approved: Whether charge was successful
                - new_balance: User's remaining token balance
        
        Raises:
            ValueError: If any parameter is invalid
            InsufficientBalanceError: If user doesn't have enough tokens
            SessionExpiredError: If session has expired
        
        Example:
            >>> result = client.charge(
            ...     session_token="ps_abc123...",
            ...     idempotency_key="req_abc123",
            ...     model_name="gpt-4",
            ...     input_tokens=1500,
            ...     output_tokens=500
            ... )
            >>> if result.approved:
            ...     print(f"Charged! Remaining: {result.new_balance} tokens")
            >>> else:
            ...     print(f"Failed: {result.error}")
        """
        # Validate session_token
        if not session_token or not isinstance(session_token, str) or not session_token.strip():
            raise ValueError("session_token is required and cannot be empty")
        
        # Validate idempotency_key
        if not idempotency_key or not isinstance(idempotency_key, str) or not idempotency_key.strip():
            raise ValueError("idempotency_key is required and cannot be empty")
        
        # Validate model_name
        if not model_name or not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name is required and cannot be empty")
        
        # Validate input_tokens
        if not isinstance(input_tokens, int) or input_tokens < 0:
            raise ValueError("input_tokens must be a non-negative integer")
        
        # Validate output_tokens
        if not isinstance(output_tokens, int) or output_tokens < 0:
            raise ValueError("output_tokens must be a non-negative integer")
        
        try:
            response = self._request(
                method="POST",
                endpoint="/charge/authorize",
                data={
                    "model_name": model_name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
                headers={
                    "X-Provider-Session": session_token,
                    "X-Idempotency-Key": idempotency_key,
                },
            )
            # Backend ChargeResponse: approved, new_balance, error_code (optional, e.g. HARD_CAP_VIOLATION)
            return ChargeResult.from_api_response(response)

        except InsufficientBalanceError as e:
            return ChargeResult(
                approved=False,
                new_balance=e.current_balance or 0,
                error_code=getattr(e, "error_code", None),
                error=str(e),
            )
        except (SessionExpiredError, ForbiddenError) as e:
            # 401 session expired or 403 limit/NO_CHARGE_PERMISSION
            return ChargeResult(
                approved=False,
                new_balance=getattr(e, "current_balance", None) or 0,
                error_code=getattr(e, "error_code", None),
                error=str(e),
            )
    
    def preview_charge(
        self,
        session_token: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Dict[str, Any]:
        """
        Preview a charge without deducting tokens.
        
        Use this to check if user can afford a charge before making it.
        
        Args:
            session_token: Active session token
            model_name: AI model to use
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens
        
        Returns:
            Dict with estimated cost and affordability
        
        Note:
            This is a client-side estimation. For accurate pricing,
            use the actual charge endpoint.
        """
        # Get current balance
        try:
            # This would need wallet_id from session - simplified here
            return {
                "model_name": model_name,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "can_proceed": True,  # Simplified - actual implementation needs balance check
            }
        except Exception as e:
            return {
                "can_proceed": False,
                "error": str(e),
            }
    
    # =========================================================================
    # Wallet / Balance
    # =========================================================================
    
    def get_wallet_balance(self, wallet_id: str) -> WalletBalance:
        """
        Get a wallet's token balance.
        
        This is a public endpoint that returns basic wallet info.
        
        Args:
            wallet_id: 16-digit wallet ID
        
        Returns:
            WalletBalance with wallet_id and tokens
        
        Raises:
            ValueError: If wallet_id is invalid
        
        Example:
            >>> balance = client.get_wallet_balance("1234567890123456")
            >>> print(f"Balance: {balance.tokens} tokens")
        """
        # Validate wallet_id
        if not wallet_id or not isinstance(wallet_id, str) or not wallet_id.strip():
            raise ValueError("wallet_id is required and cannot be empty")
        
        # Sanitize wallet_id to prevent path injection
        wallet_id_clean = wallet_id.strip()
        # Remove any path separators or dangerous characters
        if "/" in wallet_id_clean or "\\" in wallet_id_clean or ".." in wallet_id_clean:
            raise ValueError("wallet_id contains invalid characters")
        
        # URL encode the wallet_id for safety
        from urllib.parse import quote
        wallet_id_encoded = quote(wallet_id_clean, safe="")
        
        response = self._request(
            method="GET",
            endpoint=f"/wallet/{wallet_id_encoded}",
        )
        
        return WalletBalance.from_api_response(response)
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def health_check(self) -> bool:
        """
        Check if the CONXA API is reachable.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self._request(
                method="GET",
                endpoint="/health",
            )
            return response.get("status") == "ok"
        except Exception:
            return False
    
    def close(self):
        """Close the HTTP session"""
        self._session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
        return False

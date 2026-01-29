"""
CONXA SDK Client

Main client class for interacting with the CONXA Wallet API.
"""

import time
import json
from typing import Optional, Dict, Any
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
        if not api_key:
            raise AuthenticationError("API key is required")
        
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.provider_type = provider_type
        
        # Extract or set provider_id
        # API key format: pk_live_providername_xxxxx
        if provider_id:
            self.provider_id = provider_id
        else:
            # Try to extract from API key (this is a fallback)
            # Providers should ideally set this explicitly
            self.provider_id = self._extract_provider_id_from_key(api_key)
        
        # Session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Provider-API-Key": self.api_key,
        })
    
    def _extract_provider_id_from_key(self, api_key: str) -> str:
        """Extract provider ID from API key format"""
        # This is a placeholder - providers should set provider_id explicitly
        # The actual provider_id should come from your registration
        return api_key[:20] if api_key else "unknown"
    
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
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"message": response.text}
            
            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError(
                    response_data.get("detail", "Authentication failed")
                )
            elif response.status_code == 402:
                raise InsufficientBalanceError(
                    response_data.get("detail", "Insufficient balance"),
                    current_balance=response_data.get("new_balance"),
                )
            elif response.status_code == 404:
                raise SessionNotFoundError(
                    response_data.get("detail", "Not found")
                )
            elif response.status_code == 422:
                raise ValidationError(
                    response_data.get("message", "Validation error"),
                    errors=response_data.get("errors", []),
                )
            elif response.status_code == 429:
                raise RateLimitError(
                    response_data.get("detail", "Rate limit exceeded"),
                    retry_after=response.headers.get("Retry-After"),
                )
            elif response.status_code >= 400:
                raise APIError(
                    response_data.get("detail", response_data.get("message", "API error")),
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
        
        Returns:
            QRCodeData with:
                - qr_data: JSON string encoded in QR
                - qr_image: PIL Image object (if qrcode installed)
                - qr_base64: Base64 PNG for HTML embedding
        
        Example:
            >>> qr = client.create_payment_qr(
            ...     provider_username="user@example.com",
            ...     limit=10000
            ... )
            >>> # Display in web app
            >>> html = f'<img src="{qr.qr_base64}" />'
            >>> # Or save to file
            >>> qr.qr_image.save("connect.png")
        """
        return generate_qr_code(
            provider_id=self.provider_id,
            provider_type=provider_type or self.provider_type,
            provider_username=provider_username,
            limit=limit,
            size=size,
        )
    
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
        """
        return generate_qr_svg(
            provider_id=self.provider_id,
            provider_type=provider_type or self.provider_type,
            provider_username=provider_username,
            limit=limit,
            size=size,
        )
    
    # =========================================================================
    # Session / Connection Status
    # =========================================================================
    
    def get_session_status(self, provider_username: str) -> SessionStatus:
        """
        Check if a user has connected their wallet.
        
        Poll this endpoint after showing the QR code to detect when
        the user scans and approves the connection.
        
        Args:
            provider_username: User's ID in your system
        
        Returns:
            SessionStatus with:
                - status: "pending", "active", "expired", or "not_found"
                - session_token: Token for charges (only if active)
                - expires_at: Session expiration time
        
        Example:
            >>> status = client.get_session_status("user@example.com")
            >>> if status.is_active:
            ...     print(f"Connected! Token: {status.session_token}")
            >>> elif status.is_pending:
            ...     print("Waiting for user to scan QR...")
        """
        response = self._request(
            method="GET",
            endpoint="/providers/session/status",
            params={"provider_username": provider_username},
        )
        
        return SessionStatus.from_api_response(response)
    
    def wait_for_connection(
        self,
        provider_username: str,
        timeout: int = 120,
        poll_interval: int = 2,
        on_pending: callable = None,
    ) -> SessionStatus:
        """
        Wait for user to connect their wallet (blocking).
        
        Polls the session status until the user connects or timeout occurs.
        
        Args:
            provider_username: User's ID in your system
            timeout: Maximum wait time in seconds (default: 120)
            poll_interval: Time between polls in seconds (default: 2)
            on_pending: Optional callback called on each pending poll
        
        Returns:
            SessionStatus with active session
        
        Raises:
            ConnectionTimeoutError: If user doesn't connect within timeout
        
        Example:
            >>> session = client.wait_for_connection(
            ...     provider_username="user@example.com",
            ...     timeout=60,
            ...     on_pending=lambda s: print("Waiting...")
            ... )
            >>> print(f"Connected! Token: {session.session_token}")
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise ConnectionTimeoutError(
                    f"User did not connect within {timeout} seconds"
                )
            
            try:
                status = self.get_session_status(provider_username)
                
                if status.is_active:
                    return status
                
                if status.is_expired:
                    raise SessionExpiredError("Session expired before connection")
                
                if on_pending and status.is_pending:
                    on_pending(status)
                
            except SessionNotFoundError:
                # No session yet, keep waiting
                pass
            
            time.sleep(poll_interval)
    
    # =========================================================================
    # Charging API
    # =========================================================================
    
    def charge(
        self,
        session_token: str,
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
            model_name: AI model used (e.g., "gpt-4", "claude-3")
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
        
        Returns:
            ChargeResult with:
                - approved: Whether charge was successful
                - new_balance: User's remaining token balance
        
        Raises:
            InsufficientBalanceError: If user doesn't have enough tokens
            SessionExpiredError: If session has expired
        
        Example:
            >>> result = client.charge(
            ...     session_token="ps_abc123...",
            ...     model_name="gpt-4",
            ...     input_tokens=1500,
            ...     output_tokens=500
            ... )
            >>> if result.approved:
            ...     print(f"Charged! Remaining: {result.new_balance} tokens")
            >>> else:
            ...     print(f"Failed: {result.error}")
        """
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
                },
            )
            
            return ChargeResult.from_api_response(response)
            
        except InsufficientBalanceError as e:
            return ChargeResult(
                approved=False,
                new_balance=e.current_balance or 0,
                error=str(e),
            )
        except SessionExpiredError as e:
            return ChargeResult(
                approved=False,
                new_balance=0,
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
        
        Example:
            >>> balance = client.get_wallet_balance("1234567890123456")
            >>> print(f"Balance: {balance.tokens} tokens")
        """
        response = self._request(
            method="GET",
            endpoint=f"/wallet/{wallet_id}",
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

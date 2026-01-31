"""
CONXA SDK Data Models

Data classes representing API responses and SDK objects.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
from enum import Enum


class ConnectionStatus(str, Enum):
    """Status of a provider session/connection"""
    
    PENDING = "pending"       # Waiting for user to connect
    ACTIVE = "active"         # User connected, session is active
    EXPIRED = "expired"       # Session has expired
    NOT_FOUND = "not_found"   # No session found


@dataclass
class QRCodeData:
    """
    QR code generation result
    
    Attributes:
        qr_data: JSON string to encode in QR code
        qr_image: PIL Image object of the QR code (if qrcode library installed)
        qr_base64: Base64 encoded PNG image for embedding in HTML
        provider_id: Provider ID included in QR
        provider_type: Provider type (api/web)
        provider_username: User's ID in provider's system
        created_at: Timestamp when QR was created (for expiration tracking)
        expires_at: Timestamp when QR expires (if expires_in was set)
    """
    
    qr_data: str
    qr_image: Any = None  # PIL.Image.Image
    qr_base64: str = ""
    provider_id: str = ""
    provider_type: str = ""
    provider_username: str = ""
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if QR code has expired"""
        if self.expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        if isinstance(self.expires_at, str):
            self.expires_at = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        return self.expires_at < now
    
    def is_valid_base64(self) -> bool:
        """Check if qr_base64 is valid and can be used in HTML"""
        return (
            bool(self.qr_base64) and 
            len(self.qr_base64) > 0 and
            self.qr_base64.startswith("data:image/png;base64,") and
            len(self.qr_base64) > len("data:image/png;base64,")
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excluding image object)"""
        return {
            "qr_data": self.qr_data,
            "qr_base64": self.qr_base64,
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "provider_username": self.provider_username,
        }
    
    def to_json_safe_dict(self) -> dict:
        """
        Convert to dictionary safe for JSON serialization.
        
        Ensures qr_base64 is properly formatted and validates it before returning.
        Use this when sending QR data through API responses.
        
        Returns:
            Dictionary with validated qr_base64 ready for JSON serialization
            
        Raises:
            ValueError: If qr_base64 is invalid
        """
        # Validate before returning
        if not self.is_valid_base64():
            raise ValueError(
                f"Invalid QR code base64 data. "
                f"Expected format: 'data:image/png;base64,...' "
                f"Got: {self.qr_base64[:50] if self.qr_base64 else 'empty'}..."
            )
        
        return {
            "qr_data": self.qr_data,
            "qr_base64": self.qr_base64,  # Already validated, safe for JSON
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "provider_username": self.provider_username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
    
    def get_html_img_tag(self) -> str:
        """
        Get a ready-to-use HTML img tag with the QR code.
        
        Returns:
            HTML img tag string with validated base64 data URL
            
        Raises:
            ValueError: If qr_base64 is invalid
        """
        if not self.is_valid_base64():
            raise ValueError(
                f"Cannot create HTML img tag: Invalid QR code base64 data. "
                f"Expected format: 'data:image/png;base64,...'"
            )
        
        return f'<img src="{self.qr_base64}" alt="CONXA QR Code" />'


@dataclass
class SessionStatus:
    """
    Provider session status response
    
    Attributes:
        status: Connection status (pending, active, expired, not_found)
        session_token: Session token for making charges (only if active)
        expires_at: Session expiration time (only if active)
    """
    
    status: ConnectionStatus
    session_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    @property
    def is_active(self) -> bool:
        """Check if session is active and ready for charges"""
        return self.status == ConnectionStatus.ACTIVE and self.session_token is not None
    
    @property
    def is_pending(self) -> bool:
        """Check if waiting for user to connect"""
        return self.status == ConnectionStatus.PENDING
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired"""
        return self.status == ConnectionStatus.EXPIRED
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "status": self.status.value if isinstance(self.status, ConnectionStatus) else self.status,
            "session_token": self.session_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
    
    @classmethod
    def from_api_response(cls, data: dict) -> "SessionStatus":
        """Create from API response"""
        status_str = data.get("status", "not_found")
        try:
            status = ConnectionStatus(status_str)
        except ValueError:
            status = ConnectionStatus.NOT_FOUND
        
        expires_at = None
        if data.get("expires_at"):
            try:
                expires_at = datetime.fromisoformat(
                    data["expires_at"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass
        
        return cls(
            status=status,
            session_token=data.get("session_token"),
            expires_at=expires_at,
        )


@dataclass
class ChargeResult:
    """
    Result of a charge/authorize request (aligned with backend ChargeResponse).

    Attributes:
        approved: Whether the charge was approved
        new_balance: User's new token balance after charge
        error_code: Optional backend error code (e.g. HARD_CAP_VIOLATION, NO_CHARGE_PERMISSION)
        error: Error message if charge failed (for exception-derived results)
    """

    approved: bool
    new_balance: int
    error_code: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "approved": self.approved,
            "new_balance": self.new_balance,
            "error_code": self.error_code,
            "error": self.error,
        }

    @classmethod
    def from_api_response(cls, data: dict, error: str = None) -> "ChargeResult":
        """Create from API response (backend ChargeResponse: approved, new_balance, error_code)."""
        return cls(
            approved=data.get("approved", False),
            new_balance=data.get("new_balance", 0),
            error_code=data.get("error_code"),
            error=error,
        )


@dataclass
class WalletBalance:
    """
    User's wallet balance
    
    Attributes:
        wallet_id: User's wallet ID
        tokens: Current token balance
    """
    
    wallet_id: str
    tokens: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "wallet_id": self.wallet_id,
            "tokens": self.tokens,
        }
    
    @classmethod
    def from_api_response(cls, data: dict) -> "WalletBalance":
        """Create from API response"""
        return cls(
            wallet_id=data.get("wallet_id", ""),
            tokens=data.get("tokens", 0),
        )


@dataclass
class ProviderInfo:
    """
    Provider information
    
    Attributes:
        provider_id: Unique provider ID
        name: Provider name
        type: Provider type (api/web)
        api_key: Provider's API key (masked)
    """
    
    provider_id: str
    name: str
    type: str
    api_key: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "type": self.type,
        }

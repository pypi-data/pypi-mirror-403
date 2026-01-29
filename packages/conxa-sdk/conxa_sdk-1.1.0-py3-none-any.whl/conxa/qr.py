"""
CONXA SDK QR Code Generation

Utilities for generating QR codes that users scan to connect their wallet.
"""

import json
import base64
import warnings
from io import BytesIO
from typing import Any, Optional

from .models import QRCodeData


def generate_qr_data(
    provider_id: str,
    provider_type: str,
    provider_username: str,
    limit: Optional[float] = None,
) -> str:
    """
    Generate the JSON data to encode in the QR code.
    
    This data is what the CONXA mobile app expects when scanning.
    
    Args:
        provider_id: The provider's unique ID
        provider_type: "api" or "web"
        provider_username: User's ID in the provider's system
        limit: Optional spending limit in tokens
    
    Returns:
        JSON string to encode in QR code
    """
    qr_payload = {
        "provider_id": provider_id,
        "provider_type": provider_type,
        "provider_username": provider_username,
    }
    
    if limit is not None:
        qr_payload["limit"] = limit
    
    return json.dumps(qr_payload, separators=(",", ":"))


def generate_qr_code(
    provider_id: str,
    provider_type: str,
    provider_username: str,
    limit: Optional[float] = None,
    size: int = 300,
    border: int = 4,
) -> QRCodeData:
    """
    Generate a QR code for user to scan and connect their wallet.
    
    Args:
        provider_id: The provider's unique ID
        provider_type: "api" or "web"
        provider_username: User's ID in the provider's system
        limit: Optional spending limit in tokens
        size: QR code image size in pixels (default: 300)
        border: QR code border size (default: 4)
    
    Returns:
        QRCodeData with qr_data, qr_image (if qrcode installed), and qr_base64
    
    Note:
        Requires 'qrcode' and 'pillow' packages for image generation.
        If not installed, only qr_data will be populated.
    """
    # Generate the JSON data
    qr_data = generate_qr_data(provider_id, provider_type, provider_username, limit)
    
    # Try to generate QR image
    qr_image = None
    qr_base64 = ""
    
    try:
        # Import qrcode library
        import qrcode
        
        # Import Pillow (PIL) - required for image generation
        try:
            from PIL import Image
        except ImportError:
            try:
                import Image  # Fallback for older Pillow versions
            except ImportError:
                raise ImportError("Pillow (PIL) is required for QR code image generation")
        
        # Use qrcode.constants directly for better version compatibility
        ERROR_CORRECT_M = qrcode.constants.ERROR_CORRECT_M
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=border,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Resize to requested size
        qr_image = qr_image.resize((size, size))
        
        # Convert to base64
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        buffer.seek(0)
        image_bytes = buffer.getvalue()
        qr_base64 = f"data:image/png;base64,{base64.b64encode(image_bytes).decode('utf-8')}"
        
    except ImportError as e:
        # qrcode or pillow not installed
        warnings.warn(
            f"QR code image generation requires 'qrcode' and 'pillow' packages. "
            f"Install with: pip install qrcode[pil]. Error: {e}",
            UserWarning
        )
    except Exception as e:
        # Any other error during QR generation
        warnings.warn(
            f"Failed to generate QR code image: {e}. "
            f"QR data is still available: {qr_data}",
            UserWarning
        )
    
    return QRCodeData(
        qr_data=qr_data,
        qr_image=qr_image,
        qr_base64=qr_base64,
        provider_id=provider_id,
        provider_type=provider_type,
        provider_username=provider_username,
    )


def generate_qr_svg(
    provider_id: str,
    provider_type: str,
    provider_username: str,
    limit: Optional[float] = None,
    size: int = 300,
) -> str:
    """
    Generate QR code as SVG string.
    
    Args:
        provider_id: The provider's unique ID
        provider_type: "api" or "web"
        provider_username: User's ID in the provider's system
        limit: Optional spending limit in tokens
        size: SVG size in pixels
    
    Returns:
        SVG string of the QR code
    
    Note:
        Requires 'qrcode' package with SVG support.
    """
    qr_data = generate_qr_data(provider_id, provider_type, provider_username, limit)
    
    try:
        import qrcode
        import qrcode.image.svg
        
        # Use qrcode.constants directly for better version compatibility
        ERROR_CORRECT_M = qrcode.constants.ERROR_CORRECT_M
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create SVG image
        factory = qrcode.image.svg.SvgImage
        img = qr.make_image(image_factory=factory)
        
        # Get SVG string
        buffer = BytesIO()
        img.save(buffer)
        buffer.seek(0)
        return buffer.read().decode()
        
    except ImportError:
        raise ImportError(
            "qrcode package is required for SVG generation. "
            "Install with: pip install qrcode[pil]"
        )

"""
CONXA SDK QR Code Generation

Utilities for generating QR codes that users scan to connect their wallet.
"""

import json
import base64
from io import BytesIO
from typing import Any, Optional

import qrcode

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
        QRCodeData with qr_data, qr_image, and qr_base64
    """
    # Generate the JSON data
    qr_data = generate_qr_data(provider_id, provider_type, provider_username, limit)
    
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
    
    # Validate that image was generated successfully
    if not image_bytes or len(image_bytes) == 0:
        raise ValueError("Failed to generate QR code image: empty image data")
    
    # Encode to base64 and create data URL
    base64_encoded = base64.b64encode(image_bytes).decode('utf-8')
    if not base64_encoded:
        raise ValueError("Failed to encode QR code image to base64")
    
    qr_base64 = f"data:image/png;base64,{base64_encoded}"
    
    # Final validation that qr_base64 is valid
    if not qr_base64 or not qr_base64.startswith("data:image/png;base64,"):
        raise ValueError("Failed to generate valid QR code base64 data URL")
    
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
    """
    qr_data = generate_qr_data(provider_id, provider_type, provider_username, limit)
    
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

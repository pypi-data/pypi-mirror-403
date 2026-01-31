# CONXA Python SDK

Official Python SDK for integrating CONXA Wallet payments into AI services.

## Overview

CONXA is a universal wallet for AI services. This SDK enables AI providers (ChatGPT, Claude, etc.) to:

1. **Generate QR codes** for users to connect their CONXA wallet
2. **Detect connections** when users scan and approve
3. **Charge users** for AI usage (pay-per-token)
4. **Check balances** and manage sessions

## Installation

```bash
# Install from PyPI (includes QR code generation)
pip install conxa-sdk

# From source
pip install .

# Development with examples (Flask, FastAPI)
pip install -e ".[dev,examples]"
```

## Quick Start

```python
from conxa import CONXAClient

# Initialize with your API key
client = CONXAClient(
    api_key="pk_live_your_api_key",
    provider_id="your_provider_id",
)

# 1. Generate QR code for user to scan
qr = client.create_payment_qr(
    provider_username="user@example.com",
    expires_in=10  # Optional: QR expires after 10 seconds
)
print(f"Show this QR to user: {qr.qr_base64}")

# 2. Wait for user to connect (or poll manually)
session = client.wait_for_connection(
    provider_username="user@example.com",
    timeout=120,  # Wait up to 2 minutes
    qr_data=qr,  # Pass QR data to check expiration
)
print(f"User connected! Token: {session.session_token}")

# 3. Charge for AI usage (use a unique idempotency key per logical charge)
result = client.charge(
    session_token=session.session_token,
    idempotency_key="req_abc123",  # e.g. request ID - required for retry safety
    model_name="gpt-4",
    input_tokens=1000,
    output_tokens=500,
)

if result.approved:
    print(f"Charged! New balance: {result.new_balance} tokens")
else:
    print(f"Failed: {result.error}")
```

## Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR AI SERVICE                          │
│                                                                 │
│  1. User visits your website                                    │
│     │                                                           │
│     ▼                                                           │
│  2. Generate QR: client.create_payment_qr(username, expires_in=10) │
│     │                                                           │
│     ▼                                                           │
│  3. Display QR code to user (expires after 10 seconds)         │
│     │                                                           │
│     │    ┌─────────────────────────────────┐                   │
│     │    │      CONXA Mobile App           │                   │
│     └───▶│  User scans QR & approves       │                   │
│          │  Connection established!         │                   │
│          └─────────────────────────────────┘                   │
│     │                                                           │
│     ▼                                                           │
│  4. Detect connection: client.get_session_status(username, qr_data=qr) │
│     │                                                           │
│     ▼                                                           │
│  5. For each AI request:                                        │
│     result = client.charge(session_token, idempotency_key, ...)  │
│     │                                                           │
│     ▼                                                           │
│  6. Tokens deducted from user's CONXA wallet                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## API Reference

### CONXAClient

Main client class for interacting with CONXA API.

```python
client = CONXAClient(
    api_key="pk_live_xxx",           # Required: Your API key
    provider_id="your_provider_id",   # Required: Your provider ID
    base_url="https://api.conxa.in",  # Optional: API base URL
    timeout=30,                       # Optional: Request timeout
    provider_type="api",              # Optional: "api" or "web"
)
```

### Methods

#### `create_payment_qr(provider_username, provider_type=None, limit=None, size=300, expires_in=None)`

Generate a QR code for user to scan and connect.

```python
qr = client.create_payment_qr(
    provider_username="user@example.com",
    provider_type=None,  # Optional: "api" or "web" (default: client's provider_type)
    limit=50000,         # Optional: spending limit in tokens
    size=300,            # Optional: image size in pixels
    expires_in=10,       # Optional: QR expires after N seconds (default: None)
)

# Returns QRCodeData:
# - qr.qr_data: JSON string to encode
# - qr.qr_image: PIL Image object
# - qr.qr_base64: Base64 PNG for HTML <img> tag (validated and guaranteed valid)
# - qr.created_at: Timestamp when QR was created
# - qr.expires_at: Timestamp when QR expires (if expires_in is set)
# - qr.is_expired(): Method to check if QR has expired
# - qr.is_valid_base64(): Method to check if base64 data is valid
# - qr.to_json_safe_dict(): Get validated dict safe for API responses
# - qr.get_html_img_tag(): Get ready-to-use HTML img tag
```

#### `create_payment_qr_svg(provider_username, provider_type=None, limit=None, size=300)`

Generate a QR code as an SVG string (no expiration; useful for server-rendered SVG).

```python
svg_string = client.create_payment_qr_svg(
    provider_username="user@example.com",
    provider_type=None,  # Optional: "api" or "web"
    limit=50000,
    size=300,
)
# Returns: str (SVG markup)
```

**QR Code Expiration:**

If `expires_in` is set, the QR code will automatically expire after the specified number of seconds. This is useful for security and ensuring users generate fresh QR codes:

```python
# Generate QR that expires after 10 seconds
qr = client.create_payment_qr(
    provider_username="user@example.com",
    expires_in=10
)

# Check if QR has expired
if qr.is_expired():
    print("QR code expired! Generate a new one.")
    qr = client.create_payment_qr(provider_username="user@example.com", expires_in=10)

# Validate QR code before using in HTML (optional - validation is automatic)
if qr.is_valid_base64():
    html = f'<img src="{qr.qr_base64}" alt="QR Code" />'
else:
    print("Error: Invalid QR code generated")
```

**QR Code Validation:**

The SDK automatically validates all QR codes during generation to prevent browser errors. If validation fails, a `ValueError` is raised with a clear error message:

```python
try:
    qr = client.create_payment_qr(provider_username="user@example.com")
    # QR code is guaranteed to be valid at this point
    # qr.qr_base64 is always a valid data URL
except ValueError as e:
    print(f"QR generation failed: {e}")
    # Handle error appropriately
```

You can also manually check validation using `is_valid_base64()`:
```python
qr = client.create_payment_qr(provider_username="user@example.com")
if qr.is_valid_base64():
    # Safe to use in HTML
    display_qr(qr.qr_base64)
```

**Helper Methods for Integration:**

For API responses, use `to_json_safe_dict()` which validates before serialization:
```python
@app.post("/connect")
def connect():
    qr = client.create_payment_qr(provider_username=user_id)
    return qr.to_json_safe_dict()  # Validated and safe for JSON
```

For server-side HTML generation, use `get_html_img_tag()`:
```python
qr = client.create_payment_qr(provider_username=user_id)
html = qr.get_html_img_tag()  # Returns: <img src="data:image/png;base64,..." />
```

#### `get_session_status(provider_username, retry_on_rate_limit=True, max_retries=3, qr_data=None)`

Check if user has connected their wallet. Automatically handles rate limiting with exponential backoff.

```python
qr = client.create_payment_qr("user@example.com", expires_in=10)
status = client.get_session_status(
    "user@example.com",
    qr_data=qr,  # Optional: Check if QR has expired
    retry_on_rate_limit=True,  # Auto-retry on rate limits
    max_retries=3,  # Max retry attempts
)

# Returns SessionStatus:
# - status.status: "pending", "active", "expired", "not_found"
# - status.session_token: Token for charges (if active)
# - status.expires_at: Session expiration time
# - status.is_active: True if session is active and ready for charges
# - status.is_pending: True if waiting for user to connect
# - status.is_expired: True if session has expired

# Raises SessionExpiredError if QR code has expired
```

**Rate Limit Handling:**

The SDK automatically retries on rate limit errors (429) with exponential backoff. If `qr_data` is provided and the QR has expired, it will raise `SessionExpiredError` instead of polling.

#### `wait_for_connection(provider_username, timeout=120, poll_interval=2, on_pending=None, rate_limit_timeout=10, qr_data=None)`

Block until user connects or timeout. Automatically handles rate limiting and QR expiration.

```python
qr = client.create_payment_qr("user@example.com", expires_in=10)

session = client.wait_for_connection(
    provider_username="user@example.com",
    timeout=120,              # Maximum wait time in seconds
    poll_interval=2,         # Time between status checks
    on_pending=lambda s: print("Waiting..."),  # Callback on each poll
    rate_limit_timeout=10,   # Close QR after N seconds of rate limiting
    qr_data=qr,             # Optional: Check QR expiration
)

# Raises:
# - ConnectionTimeoutError: If user doesn't connect within timeout
# - SessionExpiredError: If QR expires or rate limited for too long
```

**Features:**
- Automatic retry on rate limit errors with exponential backoff
- QR expiration checking (if `qr_data` provided)
- Rate limit timeout protection (closes QR after extended rate limiting)

#### `charge(session_token, idempotency_key, model_name, input_tokens, output_tokens)`

Charge user for AI usage. Use a unique `idempotency_key` per logical charge (e.g. request ID) for exactly-once semantics on retries.

```python
result = client.charge(
    session_token="ps_xxx",
    idempotency_key="req_abc123",  # Required: unique per logical charge
    model_name="gpt-4",
    input_tokens=1000,
    output_tokens=500,
)

# Returns ChargeResult:
# - result.approved: Boolean
# - result.new_balance: Remaining tokens
# - result.error_code: Optional backend code (e.g. HARD_CAP_VIOLATION, NO_CHARGE_PERMISSION)
# - result.error: Error message (if failed)
```

#### `get_wallet_balance(wallet_id)`

Get wallet token balance (public endpoint).

```python
balance = client.get_wallet_balance("1234567890123456")
# Returns: WalletBalance(wallet_id, tokens)
```

## Exception Handling

```python
from conxa import (
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

try:
    # Generate QR with expiration
    qr = client.create_payment_qr("user@example.com", expires_in=10)
    
    # Wait for connection
    session = client.wait_for_connection("user@example.com", qr_data=qr)
    
    # Charge user
    result = client.charge(...)
    
except SessionExpiredError as e:
    print("QR code or session expired - user needs to reconnect")
    # Generate new QR code
    qr = client.create_payment_qr("user@example.com", expires_in=10)
    
except InsufficientBalanceError as e:
    print(f"User has insufficient balance: {e.current_balance} tokens")
    
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after} seconds")
    # SDK automatically retries, but you can handle manually if needed
    
except ConnectionTimeoutError:
    print("User did not connect within timeout period")
    
except AuthenticationError:
    print("Invalid API key")
    
except IdempotencyConflictError:
    print("Charge with this idempotency key already in progress - do not retry")
    
except ForbiddenError:
    print("Forbidden (e.g. spending limit exceeded or no charge permission)")
    
except CONXAError as e:
    print(f"CONXA error: {e}")
```

## Examples

See the `examples/` directory for complete integration examples:

- `basic_integration.py` - Simple command-line example
- `flask_integration.py` - Flask web app with QR display
- `fastapi_integration.py` - FastAPI app with WebSocket support

## Web Framework Integration

### Flask

```python
from flask import Flask, session, jsonify
from conxa import CONXAClient

app = Flask(__name__)
client = CONXAClient(api_key="pk_live_xxx", provider_id="xxx")

@app.route("/connect")
def connect():
    # Generate QR that expires after 10 seconds
    qr = client.create_payment_qr(
        provider_username=session["user_email"],
        expires_in=10
    )
    # Store QR data in session to check expiration
    session["qr_data"] = {
        "created_at": qr.created_at.isoformat() if qr.created_at else None,
        "expires_at": qr.expires_at.isoformat() if qr.expires_at else None,
    }
    return render_template("connect.html", qr_base64=qr.qr_base64)

@app.route("/api/chat", methods=["POST"])
def chat():
    import uuid
    result = client.charge(
        session_token=session["conxa_token"],
        idempotency_key=request.json.get("request_id", "req_" + str(uuid.uuid4())),
        model_name="gpt-4",
        input_tokens=request.json["input_tokens"],
        output_tokens=request.json["output_tokens"],
    )
    if not result.approved:
        return jsonify({"error": "Insufficient balance"}), 402
    # Process AI request...
```

### FastAPI

```python
from fastapi import FastAPI, HTTPException
from conxa import CONXAClient

app = FastAPI()
client = CONXAClient(api_key="pk_live_xxx", provider_id="xxx")

@app.post("/connect")
async def connect(user_id: str):
    # Generate QR that expires after 10 seconds
    qr = client.create_payment_qr(
        provider_username=user_id,
        expires_in=10
    )
    return {
        "qr_base64": qr.qr_base64,
        "expires_at": qr.expires_at.isoformat() if qr.expires_at else None,
    }

@app.post("/chat")
async def chat(user_id: str, message: str, qr_data: dict = None):
    # Check if QR has expired (if provided)
    qr = None
    if qr_data:
        from conxa.models import QRCodeData
        from datetime import datetime
        qr = QRCodeData(
            qr_data="",
            created_at=datetime.fromisoformat(qr_data["created_at"]) if qr_data.get("created_at") else None,
            expires_at=datetime.fromisoformat(qr_data["expires_at"]) if qr_data.get("expires_at") else None,
        )
    
    try:
        status = client.get_session_status(user_id, qr_data=qr)
    except SessionExpiredError:
        raise HTTPException(401, "QR code expired. Please generate a new one.")
    
    if not status.is_active:
        raise HTTPException(401, "User not connected")
    
    import uuid
    result = client.charge(
        session_token=status.session_token,
        idempotency_key="req_" + str(uuid.uuid4()),  # use request ID from client in production
        model_name="gpt-4",
        input_tokens=len(message) * 4,
        output_tokens=100,
    )
    if not result.approved:
        raise HTTPException(402, "Insufficient balance")
    # Process AI request...
```

## Configuration

### Environment Variables

```bash
# API Configuration
CONXA_API_KEY=pk_live_your_api_key
CONXA_PROVIDER_ID=your_provider_id
CONXA_API_URL=https://api.conxa.in  # Optional
```

### Using environment variables:

```python
import os
from conxa import CONXAClient

client = CONXAClient(
    api_key=os.getenv("CONXA_API_KEY"),
    provider_id=os.getenv("CONXA_PROVIDER_ID"),
)
```

## Advanced Features

### QR Code Expiration

QR codes can be set to expire after a specified duration for security:

```python
# Generate QR that expires after 10 seconds
qr = client.create_payment_qr(
    provider_username="user@example.com",
    expires_in=10
)

# Check expiration status
if qr.is_expired():
    # Generate new QR
    qr = client.create_payment_qr("user@example.com", expires_in=10)

# When checking status, pass QR data to validate expiration
try:
    status = client.get_session_status("user@example.com", qr_data=qr)
except SessionExpiredError:
    print("QR expired - generate a new one")
```

### QR Code Validation

The SDK automatically validates all QR codes during generation to ensure they're valid and can be safely used in HTML. This prevents browser errors like `net::ERR_INVALID_URL`:

```python
# QR codes are automatically validated during generation
try:
    qr = client.create_payment_qr(provider_username="user@example.com")
    # At this point, qr.qr_base64 is guaranteed to be valid
    # You can safely use it in HTML without additional checks
    html = f'<img src="{qr.qr_base64}" alt="QR Code" />'
except ValueError as e:
    # QR generation failed validation
    print(f"Failed to generate valid QR code: {e}")
    # Handle error appropriately
```

**Manual Validation (Optional):**

You can also manually check if a QR code is valid before using it:

```python
qr = client.create_payment_qr(provider_username="user@example.com")

# Check if base64 data is valid (optional - validation happens automatically)
if qr.is_valid_base64():
    # Safe to use in HTML
    display_qr(qr.qr_base64)
else:
    # This should never happen if generation succeeded
    print("Warning: QR code validation failed")
```

**What Gets Validated:**
- Image bytes are not empty
- Base64 encoding succeeds
- Data URL format is correct (`data:image/png;base64,...`)
- PNG file signature is valid

### Rate Limit Handling

The SDK automatically handles rate limiting with exponential backoff:

```python
# Automatic retry on rate limits (default behavior)
status = client.get_session_status(
    "user@example.com",
    retry_on_rate_limit=True,  # Auto-retry (default)
    max_retries=3,              # Max retry attempts
)

# Manual rate limit handling
try:
    status = client.get_session_status("user@example.com", retry_on_rate_limit=False)
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after} seconds")
    time.sleep(e.retry_after or 60)
    status = client.get_session_status("user@example.com")
```

### Best Practices

1. **Always set QR expiration** for security:
   ```python
   qr = client.create_payment_qr(username, expires_in=10)
   ```

2. **Pass QR data when checking status** to validate expiration:
   ```python
   status = client.get_session_status(username, qr_data=qr)
   ```

3. **Handle expiration gracefully**:
   ```python
   try:
       session = client.wait_for_connection(username, qr_data=qr)
   except SessionExpiredError:
       # Generate new QR and try again
       qr = client.create_payment_qr(username, expires_in=10)
   ```

4. **Use rate limit timeout** in `wait_for_connection`:
   ```python
   session = client.wait_for_connection(
       username,
       rate_limit_timeout=10,  # Close QR after 10s of rate limiting
       qr_data=qr
   )
   ```

5. **QR codes are automatically validated** - no need for manual checks:
   ```python
   # Validation happens automatically - just use the QR code
   qr = client.create_payment_qr(username)
   html = f'<img src="{qr.qr_base64}" alt="QR Code" />'  # Safe to use
   ```

## Testing

The SDK validates QR codes during generation. For integration testing:

- Run the examples in `examples/` (e.g. `basic_integration.py`, `flask_integration.py`, `fastapi_integration.py`).
- Use `qr.to_json_safe_dict()` in your API to ensure responses are valid for JSON and frontend use.

All QR codes generated by the SDK are validated so they work correctly in web browsers.

## Troubleshooting

If you're experiencing issues with QR code display (e.g. broken image):

1. **Verify API response:** Ensure your endpoint returns `qr_base64` as a valid data URL (`data:image/png;base64,...`). Use `qr.to_json_safe_dict()` so the payload is validated before returning.

2. **Browser checks:** In DevTools → Network, confirm the response includes `qr_base64` and that the frontend uses it as the `src` of an `<img>` (or equivalent).

3. **Handle expiration:** If the QR stops working after a short time, use `expires_in` and handle `SessionExpiredError` by generating a new QR.

## Support

- **Documentation**: https://docs.conxa.in
- **API Reference**: https://api.conxa.in/docs
- **Email**: support@conxa.in
- **GitHub Issues**: https://github.com/conxa/python-sdk/issues

## License

MIT License - see LICENSE file for details.

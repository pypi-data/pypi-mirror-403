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
# Basic installation
pip install conxa-sdk

# With QR code generation support
pip install conxa-sdk[qr]

# From source
pip install .
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
qr = client.create_payment_qr(provider_username="user@example.com")
print(f"Show this QR to user: {qr.qr_base64}")

# 2. Wait for user to connect (or poll manually)
session = client.wait_for_connection(
    provider_username="user@example.com",
    timeout=120,  # Wait up to 2 minutes
)
print(f"User connected! Token: {session.session_token}")

# 3. Charge for AI usage
result = client.charge(
    session_token=session.session_token,
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
│  2. Generate QR: client.create_payment_qr(username)             │
│     │                                                           │
│     ▼                                                           │
│  3. Display QR code to user                                     │
│     │                                                           │
│     │    ┌─────────────────────────────────┐                   │
│     │    │      CONXA Mobile App           │                   │
│     └───▶│  User scans QR & approves       │                   │
│          │  Connection established!         │                   │
│          └─────────────────────────────────┘                   │
│     │                                                           │
│     ▼                                                           │
│  4. Detect connection: client.get_session_status(username)      │
│     │                                                           │
│     ▼                                                           │
│  5. For each AI request:                                        │
│     result = client.charge(session_token, model, tokens)        │
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

#### `create_payment_qr(provider_username, limit=None, size=300)`

Generate a QR code for user to scan and connect.

```python
qr = client.create_payment_qr(
    provider_username="user@example.com",
    limit=50000,  # Optional: spending limit in tokens
    size=300,     # Optional: image size in pixels
)

# Returns QRCodeData:
# - qr.qr_data: JSON string to encode
# - qr.qr_image: PIL Image object
# - qr.qr_base64: Base64 PNG for HTML <img> tag
```

#### `get_session_status(provider_username)`

Check if user has connected their wallet.

```python
status = client.get_session_status("user@example.com")

# Returns SessionStatus:
# - status.status: "pending", "active", "expired", "not_found"
# - status.session_token: Token for charges (if active)
# - status.expires_at: Session expiration time
# - status.is_active: Boolean helper
```

#### `wait_for_connection(provider_username, timeout=120, poll_interval=2)`

Block until user connects or timeout.

```python
session = client.wait_for_connection(
    provider_username="user@example.com",
    timeout=120,
    poll_interval=2,
    on_pending=lambda s: print("Waiting..."),
)
# Raises ConnectionTimeoutError if user doesn't connect
```

#### `charge(session_token, model_name, input_tokens, output_tokens)`

Charge user for AI usage.

```python
result = client.charge(
    session_token="ps_xxx",
    model_name="gpt-4",
    input_tokens=1000,
    output_tokens=500,
)

# Returns ChargeResult:
# - result.approved: Boolean
# - result.new_balance: Remaining tokens
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
)

try:
    result = client.charge(...)
except InsufficientBalanceError as e:
    print(f"User has insufficient balance: {e.current_balance} tokens")
except SessionExpiredError:
    print("Session expired - user needs to reconnect")
except AuthenticationError:
    print("Invalid API key")
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
    qr = client.create_payment_qr(provider_username=session["user_email"])
    return render_template("connect.html", qr_base64=qr.qr_base64)

@app.route("/api/chat", methods=["POST"])
def chat():
    result = client.charge(
        session_token=session["conxa_token"],
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
    qr = client.create_payment_qr(provider_username=user_id)
    return {"qr_base64": qr.qr_base64}

@app.post("/chat")
async def chat(user_id: str, message: str):
    status = client.get_session_status(user_id)
    if not status.is_active:
        raise HTTPException(401, "User not connected")
    
    result = client.charge(
        session_token=status.session_token,
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

## Support

- **Documentation**: https://docs.conxa.in
- **API Reference**: https://api.conxa.in/docs
- **Email**: support@conxa.in
- **GitHub Issues**: https://github.com/conxa/python-sdk/issues

## License

MIT License - see LICENSE file for details.

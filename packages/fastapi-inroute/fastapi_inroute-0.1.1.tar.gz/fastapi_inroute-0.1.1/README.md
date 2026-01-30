# fastapi-inroute

**WebSocket-based request forwarding for FastAPI applications**

Develop and debug webhook handlers locally by forwarding requests from test/staging deployments to your development machine. Run the same code in deployments (server mode) and locally (client mode).

## Why?

When building webhook-based applications (GitHub webhooks, Stripe payments, Twilio SMS, etc.), you need a public URL for testing. FastAPI InRoute eliminates the need for ngrok or other tunneling services by:

1. **Deploying your app in server mode** - receives webhooks at a public URL
2. **Running the same code locally in client mode** - processes webhooks with full debugging capabilities
3. **Forwarding requests via WebSocket** - server sends requests to your local client, client processes and returns responses

## Quick Start

### Installation

```bash
pip install fastapi-inroute
```

### Your Application

```python
# app.py - Same code for production AND local development
from fastapi import FastAPI, Request
from fastapi_inroute import setup_inroute

app = FastAPI()

@app.post("/webhook/github")
async def github_webhook(request: Request):
    payload = await request.json()
    print(f"Processing webhook: {payload}")
    return {"status": "processed"}

# Setup InRoute (mode determined by environment variables)
setup_inroute(app)
```

### Test/Staging Deployment

```bash
# Set environment variables in your hosting platform
export FASTAPI_INROUTE_IS_SERVER=true
export FASTAPI_INROUTE_IS_CLIENT=false

# Deploy and run
uvicorn app:app --host 0.0.0.0 --port 8000
```

Configure your webhook provider (GitHub, Stripe, etc.) to send webhooks to your test/staging deployment:
```
https://your-test-app.com/webhook/github
```

### Local Development

```bash
# Set environment variables locally
export FASTAPI_INROUTE_IS_SERVER=false
export FASTAPI_INROUTE_IS_CLIENT=true
export FASTAPI_INROUTE_SERVER_URL=wss://your-test-app.com/inroute

# Run the SAME code locally
uvicorn app:app --reload
```

Now when webhooks arrive at your test deployment URL, they'll be forwarded to your local machine for processing! Set breakpoints, add logging, modify code - all while handling real webhook payloads in a safe development environment.

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│          Test/Staging Deployment (Server Mode)           │
│                                                          │
│  GitHub/Stripe ──▶ FastAPI App ──▶ WebSocket           │
│  Webhook              (captures)      (forwards)         │
│                                          │               │
└──────────────────────────────────────────┼───────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────┼───────────────┐
│                                          │               │
│           Local Development (Client Mode)                │
│                                                          │
│              WebSocket ──▶ FastAPI App ──▶ Process      │
│              (receives)    (same code)     (debug!)      │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Features

- ✅ **Same codebase** for test deployments and local development
- ✅ **No tunneling services** required (no ngrok, localtunnel, etc.)
- ✅ **Full debugging** capabilities on local machine
- ✅ **Real webhook payloads** from third-party services
- ✅ **WebSocket-based** forwarding with automatic reconnection
- ✅ **Simple setup** with environment variables
- ✅ **Built for FastAPI** - seamless integration

## Use Cases

- **Webhook Development**: GitHub, Stripe, Twilio, SendGrid, etc.
- **OAuth Callbacks**: Test OAuth flows locally
- **Payment Processing**: Debug payment webhooks (Stripe, PayPal)
- **IoT Applications**: Device-to-server communication
- **Third-Party Integrations**: Any service that requires a public URL

## Configuration

### Environment Variables

| Variable | Description | Server Mode | Client Mode |
|----------|-------------|-------------|-------------|
| `FASTAPI_INROUTE_IS_SERVER` | Enable server mode | `true` | `false` |
| `FASTAPI_INROUTE_IS_CLIENT` | Enable client mode | `false` | `true` |
| `FASTAPI_INROUTE_SERVER_URL` | WebSocket server URL | - | `wss://your-app.com/inroute` |
| `WEBSOCKET_FORWARD_SKIP_PATHS` | Paths to skip forwarding | `/inroute,/health,/docs` | - |
| `WEBSOCKET_FORWARD_DEBUG` | Enable debug logging | `true` (optional) | `true` (optional) |

### Server Mode Endpoints

When running in server mode, these endpoints are automatically added:

- **`/inroute`** - WebSocket endpoint for client connections
- **`/connections`** - Monitor active client connections

## Example

See the [`example/`](example/) directory for a complete working example with detailed instructions.

## Documentation

- **[Quick Start Guide](https://github.com/PuneetUdhayan/fastapi-inroute/blob/main/QUICK_START.md)** - Get started in 5 minutes
- **[Usage Guide](https://github.com/PuneetUdhayan/fastapi-inroute/blob/main/USAGE_GUIDE.md)** - Comprehensive documentation
- **[Example Application](https://github.com/PuneetUdhayan/fastapi-inroute/blob/main/example/demo.py)** - Working example

## Requirements

- Python 3.11+
- FastAPI 0.128.0+
- websockets 16.0+

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

---

**Note**: This package is designed for development and testing environments only. It should NOT be used for production traffic. For production deployments, use proper load balancers, API gateways, or direct webhook handling.

Made with Bob 🤖
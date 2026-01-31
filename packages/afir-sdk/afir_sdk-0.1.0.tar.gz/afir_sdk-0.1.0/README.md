# AFIR SDK - Python SDK for API Failure Recorder

A lightweight Python SDK for monitoring and tracking API failures in your web applications.

## Installation

### Using pip
```bash
pip install afir-sdk
```

### Using uv
```bash
uv add afir-sdk
```

## Quick Start

### FastAPI Integration

```python
from fastapi import FastAPI
from afir_sdk import AFIRConfig
from afir_sdk.middleware.fastapi import AFIRMiddleware

# Configure the SDK
config = AFIRConfig(
    api_key="your-api-key",
    endpoint="http://localhost:8000/api/v1",  # Your AFIR server
    service_name="my-api",
    environment="prod"
)

# Create your app
app = FastAPI()

# Add the middleware
app.add_middleware(AFIRMiddleware, config=config)

# Your routes here
@app.get("/users/{user_id}")
def get_user(user_id: int):
    # If this returns a 4xx/5xx, it will be tracked automatically
    return {"user_id": user_id}
```

### Manual Event Tracking

```python
from afir_sdk import AFIRClient, AFIRConfig

config = AFIRConfig(
    api_key="your-api-key",
    service_name="my-service",
    environment="prod"
)

client = AFIRClient(config)

# Track an event manually
client.track_event(
    method="POST",
    path="/api/payment",
    status_code=500,
    latency_ms=1500,
    error_payload={"error": "Payment gateway timeout"}
)

# Always shutdown gracefully
client.shutdown()
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key` | str | *required* | Your AFIR API key |
| `endpoint` | str | `http://localhost:8000/api/v1` | AFIR server URL |
| `service_name` | str | `unknown-service` | Name of your service |
| `environment` | str | `dev` | Environment (prod, staging, dev) |
| `enabled` | bool | `True` | Enable/disable tracking |
| `batch_size` | int | `10` | Events per batch |
| `flush_interval` | float | `5.0` | Seconds between flushes |
| `ignored_paths` | list | `["/health", "/healthz", ...]` | Paths to skip |
| `min_status_code` | int | `400` | Minimum status to track |

## Features

- ✅ Automatic failure detection (4xx/5xx responses)
- ✅ Request batching for efficiency
- ✅ Background thread for non-blocking sends
- ✅ Correlation ID support for tracing
- ✅ Automatic header redaction (Authorization, Cookie)
- ✅ Graceful shutdown with flush

## License

MIT

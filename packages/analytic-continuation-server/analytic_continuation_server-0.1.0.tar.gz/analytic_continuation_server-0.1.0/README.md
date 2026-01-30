# Analytic Continuation Server

FastAPI server for domain coloring visualization, coordinate transforms, Laurent series fitting, and analytic continuation.

## Features

- **Coordinate Transforms**: Convert between screen and logical (complex plane) coordinates
- **Meromorphic Function Building**: Construct expressions from zeros and poles
- **Domain Coloring**: Generate visualization images (requires py-domaincolor)
- **Laurent Series Fitting**: Fit conformal maps to Jordan curves
- **Analytic Continuation**: Compute Schwarz reflection compositions
- **Session Management**: Track progress and recover interrupted computations
- **WebGL Support**: Export data optimized for GPU rendering

## Installation

```bash
pip install analytic-continuation-server
```

With domain coloring support:

```bash
pip install analytic-continuation-server[domaincolor]
```

## Quick Start

### As a CLI

Start the server:

```bash
serve-analytic-continuation --port 8000
```

With custom CORS origins:

```bash
serve-analytic-continuation --cors-origin https://myapp.com --cors-origin https://api.myapp.com
```

Disable optional features:

```bash
serve-analytic-continuation --disable-domaincolor --disable-laurent
```

Using a config file:

```bash
serve-analytic-continuation --config server-config.json
```

Or with uvicorn directly:

```bash
uvicorn analytic_continuation_server:app --reload
```

### As a Library

Use the package as an importable library in your own FastAPI application:

```python
from analytic_continuation_server import create_app, ServerConfig

# Create with custom configuration
config = ServerConfig(
    cors_origins=["https://myapp.com"],
    enable_domaincolor=True,
    enable_laurent=True,
    log_level="debug",
)
app = create_app(config)

# Or use a dict for quick configuration
app = create_app({
    "cors_origins": ["https://myapp.com"],
    "debug": True,
})

# Or use environment variables (prefix: ACS_)
# ACS_CORS_ORIGINS=https://myapp.com,https://api.myapp.com
# ACS_ENABLE_DOMAINCOLOR=true
# ACS_LOG_LEVEL=debug
app = create_app()  # Reads from environment
```

### Mount Specific Routes

If you only need specific functionality, mount individual routers:

```python
from fastapi import FastAPI
from analytic_continuation_server.routes import laurent_router, health_router, transform_router

my_app = FastAPI(title="My Math API")

# Mount only the routes you need
my_app.include_router(health_router)
my_app.include_router(transform_router)
my_app.include_router(laurent_router, prefix="/api/laurent")
```

Available routers:
- `health_router` - `/api/health` endpoints
- `transform_router` - `/api/transform/*` coordinate transformation endpoints
- `meromorphic_router` - `/api/meromorphic/*` function building endpoints
- `domaincolor_router` - `/api/domaincolor` image generation (requires py-domaincolor)
- `laurent_router` - `/api/laurent/*` Laurent fitting pipeline
- `session_router` - `/api/session/*` session management

## Configuration

### ServerConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cors_origins` | `list[str]` | `["*"]` | Allowed CORS origins |
| `enable_domaincolor` | `bool` | `True` | Enable domain coloring endpoints |
| `enable_laurent` | `bool` | `True` | Enable Laurent fitting endpoints |
| `log_level` | `str` | `"info"` | Logging level |
| `title` | `str` | `"Analytic Continuation Server"` | API title |
| `description` | `str` | ... | API description |
| `version` | `str` | `"0.1.0"` | API version |
| `debug` | `bool` | `False` | Enable debug mode |

### Environment Variables

All configuration options can be set via environment variables with the `ACS_` prefix:

| Variable | Example |
|----------|---------|
| `ACS_CORS_ORIGINS` | `"https://myapp.com,https://api.myapp.com"` |
| `ACS_ENABLE_DOMAINCOLOR` | `"true"` or `"false"` |
| `ACS_ENABLE_LAURENT` | `"true"` or `"false"` |
| `ACS_LOG_LEVEL` | `"debug"`, `"info"`, `"warning"`, `"error"` |
| `ACS_DEBUG` | `"true"` or `"false"` |

### Config File Format

```json
{
    "cors_origins": ["https://myapp.com"],
    "enable_domaincolor": true,
    "enable_laurent": true,
    "log_level": "info",
    "debug": false
}
```

## CLI Options

```
usage: serve-analytic-continuation [-h] [--host HOST] [--port PORT] [--reload]
                                   [--workers WORKERS]
                                   [--log-level {debug,info,warning,error,critical}]
                                   [--cors-origin CORS_ORIGINS] [--config FILE]
                                   [--disable-domaincolor] [--disable-laurent]
                                   [--debug] [--title TITLE]
                                   [--version-tag VERSION]

Options:
  --host HOST           Host to bind to (default: 0.0.0.0)
  --port PORT           Port to bind to (default: 8000)
  --reload              Enable auto-reload for development
  --workers WORKERS     Number of worker processes (default: 1)
  --log-level LEVEL     Log level (default: info)
  --cors-origin ORIGIN  Allowed CORS origin (can be specified multiple times)
  --config FILE         Path to JSON configuration file
  --disable-domaincolor Disable domain coloring endpoints
  --disable-laurent     Disable Laurent series fitting endpoints
  --debug               Enable debug mode
  --title TITLE         API title for OpenAPI docs
  --version-tag VERSION API version tag
```

## API Overview

| Endpoint Group | Description |
|----------------|-------------|
| `/api/health` | Health check |
| `/api/transform/*` | Coordinate transformations |
| `/api/meromorphic/*` | Function building |
| `/api/domaincolor` | Image generation |
| `/api/laurent/*` | Laurent fitting pipeline |
| `/api/session/*` | Session management |

## Example Usage

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# Health check
response = client.get("/api/health")
print(response.json())
# {'status': 'ok', 'version': '0.1.0'}

# Build a meromorphic function
response = client.post("/api/meromorphic/build", json={
    "zeros": [{"x": 1, "y": 0}, {"x": -1, "y": 0}],
    "poles": [{"x": 0, "y": 1}, {"x": 0, "y": -1}],
    "coords": "logical"
})
print(response.json())
# {"expression": "(z-1)*(z+1)/((z-i)*(z+i))", ...}

# Transform a point
response = client.post("/api/transform/point", json={
    "point": {"x": 500, "y": 200},
    "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
    "direction": "to_logical"
})
print(response.json())
# {'x': 1.0, 'y': 1.0, 'index': None}
```

## Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT License

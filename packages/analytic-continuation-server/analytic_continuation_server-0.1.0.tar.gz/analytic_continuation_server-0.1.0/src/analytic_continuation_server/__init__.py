"""
Analytic Continuation Server - FastAPI server for complex analysis visualization.

This package provides a REST API for:
- Domain coloring image generation
- Coordinate transformation between screen and logical space
- Meromorphic function building from zeros and poles
- Laurent series fitting and analytic continuation
- Session management and progress tracking

Quick Start
-----------
Run the server with uvicorn::

    uvicorn analytic_continuation_server:app --reload

Or use the CLI entry point::

    serve-analytic-continuation --port 8000

API Documentation
-----------------
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Library Usage
-------------
As an importable library with custom configuration::

    from analytic_continuation_server import create_app, ServerConfig

    # Create with custom configuration
    config = ServerConfig(
        cors_origins=["https://myapp.com"],
        enable_domaincolor=True,
        log_level="debug",
    )
    app = create_app(config)

    # Or use a dict
    app = create_app({"cors_origins": ["https://myapp.com"]})

Mount specific routes in your own FastAPI app::

    from fastapi import FastAPI
    from analytic_continuation_server.routes import laurent_router, health_router

    my_app = FastAPI()
    my_app.include_router(health_router)
    my_app.include_router(laurent_router, prefix="/api/math")

Example Usage
-------------
>>> import httpx
>>> client = httpx.Client(base_url="http://localhost:8000")
>>> response = client.get("/api/health")
>>> response.json()
{'status': 'ok', 'version': '0.1.0'}

>>> # Transform a point
>>> response = client.post("/api/transform/point", json={
...     "point": {"x": 500, "y": 200},
...     "params": {"offset_x": 400, "offset_y": 300, "scale_x": 100},
...     "direction": "to_logical"
... })
>>> response.json()
{'x': 1.0, 'y': 1.0, 'index': None}
"""

# Application factory and default instance
from .app import app, create_app

# Configuration
from .config import ServerConfig, load_config_from_env

# Route modules for selective mounting
from . import routes

# Models for type hints and custom usage
from .models import (
    # Base models
    PointModel,
    ComplexModel,
    TransformParamsModel,
    ViewBoundsModel,
    SingularityModel,
    SplineParametersModel,
    SplineExportModel,
    # Request models
    TransformPointRequest,
    TransformPointsRequest,
    DomainColorRequest,
    MeromorphicRequest,
    LaurentFitRequest,
    WebGLRenderDataRequest,
    SessionStartRequest,
    # Response models
    MeromorphicResponse,
    LaurentFitResponse,
    WebGLRenderDataResponse,
    SessionResponse,
    ContinuationDefinition,
)

__version__ = "0.1.0"
__all__ = [
    # Application
    "app",
    "create_app",
    # Configuration
    "ServerConfig",
    "load_config_from_env",
    # Route module (for accessing individual routers)
    "routes",
    # Base models
    "PointModel",
    "ComplexModel",
    "TransformParamsModel",
    "ViewBoundsModel",
    "SingularityModel",
    "SplineParametersModel",
    "SplineExportModel",
    # Request models
    "TransformPointRequest",
    "TransformPointsRequest",
    "DomainColorRequest",
    "MeromorphicRequest",
    "LaurentFitRequest",
    "WebGLRenderDataRequest",
    "SessionStartRequest",
    # Response models
    "MeromorphicResponse",
    "LaurentFitResponse",
    "WebGLRenderDataResponse",
    "SessionResponse",
    "ContinuationDefinition",
]

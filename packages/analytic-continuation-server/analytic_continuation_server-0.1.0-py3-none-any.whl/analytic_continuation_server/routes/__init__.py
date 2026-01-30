"""
API Route modules for the Analytic Continuation Server.

Routes are organized by domain:
- health: Health check and API info endpoints
- transform: Coordinate transformation endpoints
- meromorphic: Meromorphic function building endpoints
- domaincolor: Domain coloring image generation
- laurent: Laurent series fitting and inversion pipeline
- session: Session management and progress tracking

Usage
-----
Import routers for use with create_app (default behavior)::

    from analytic_continuation_server import create_app
    app = create_app()  # Includes all routers automatically

Mount specific routers in your own FastAPI app::

    from fastapi import FastAPI
    from analytic_continuation_server.routes import laurent_router, health_router

    my_app = FastAPI()
    my_app.include_router(health_router)
    my_app.include_router(laurent_router, prefix="/api/math")

Available routers::

    health_router      - /api/health endpoints
    transform_router   - /api/transform/* endpoints
    meromorphic_router - /api/meromorphic/* endpoints
    domaincolor_router - /api/domaincolor endpoints (requires py-domaincolor)
    laurent_router     - /api/laurent/* endpoints
    session_router     - /api/session/* endpoints
"""

from .health import router as health_router
from .transform import router as transform_router
from .meromorphic import router as meromorphic_router
from .domaincolor import router as domaincolor_router
from .laurent import router as laurent_router
from .session import router as session_router

__all__ = [
    "health_router",
    "transform_router",
    "meromorphic_router",
    "domaincolor_router",
    "laurent_router",
    "session_router",
]

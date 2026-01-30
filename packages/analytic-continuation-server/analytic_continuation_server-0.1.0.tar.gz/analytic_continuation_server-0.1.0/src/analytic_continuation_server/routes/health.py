"""
Health check and root API endpoints.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Analytic Continuation Server",
        "version": "0.1.0",
        "endpoints": {
            "transform": "/api/transform/*",
            "domaincolor": "/api/domaincolor",
            "meromorphic": "/api/meromorphic/*",
            "laurent": "/api/laurent/*",
            "session": "/api/session/*",
            "continuation": "/api/continuation/*",
            "health": "/api/health",
        },
    }

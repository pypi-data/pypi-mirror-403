"""
FastAPI application factory and middleware configuration.

This module provides:
- create_app(): Factory function to create configured FastAPI application
- Default app instance for direct usage

Examples
--------
Basic usage with default configuration:

>>> from analytic_continuation_server import app
>>> # Use with uvicorn: uvicorn analytic_continuation_server:app

Custom configuration:

>>> from analytic_continuation_server import create_app, ServerConfig
>>> config = ServerConfig(cors_origins=["https://myapp.com"])
>>> app = create_app(config)

Using configuration dict:

>>> app = create_app({"cors_origins": ["https://myapp.com"], "debug": True})
"""

from typing import Optional, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ServerConfig, load_config_from_env
from .routes import (
    health_router,
    transform_router,
    meromorphic_router,
    session_router,
)
from .routes.session import continuation_router


def create_app(
    config: Optional[Union[ServerConfig, dict]] = None,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Parameters
    ----------
    config : ServerConfig, dict, or None
        Server configuration. Can be:
        - ServerConfig instance
        - dict with configuration options (will be converted to ServerConfig)
        - None (uses environment variables or defaults)

    Returns
    -------
    FastAPI
        Configured FastAPI application instance.

    Examples
    --------
    Default configuration (from environment or defaults):

    >>> app = create_app()

    Using ServerConfig:

    >>> from analytic_continuation_server import ServerConfig
    >>> config = ServerConfig(
    ...     cors_origins=["https://myapp.com"],
    ...     enable_domaincolor=True,
    ...     log_level="debug",
    ... )
    >>> app = create_app(config)

    Using dict:

    >>> app = create_app({
    ...     "cors_origins": ["https://myapp.com"],
    ...     "debug": True,
    ... })

    Disable optional features:

    >>> app = create_app(ServerConfig(
    ...     enable_domaincolor=False,
    ...     enable_laurent=False,
    ... ))
    """
    # Resolve configuration
    if config is None:
        resolved_config = load_config_from_env()
    elif isinstance(config, dict):
        resolved_config = ServerConfig(**config)
    else:
        resolved_config = config

    app = FastAPI(
        title=resolved_config.title,
        description=resolved_config.description,
        version=resolved_config.version,
        debug=resolved_config.debug,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store config on app for access in routes if needed
    app.state.config = resolved_config

    # Include core routers (always enabled)
    app.include_router(health_router)
    app.include_router(transform_router)
    app.include_router(meromorphic_router)
    app.include_router(session_router)
    app.include_router(continuation_router)

    # Include optional routers based on configuration
    if resolved_config.enable_domaincolor:
        from .routes import domaincolor_router
        app.include_router(domaincolor_router)

    if resolved_config.enable_laurent:
        from .routes import laurent_router
        app.include_router(laurent_router)

    return app


# Default application instance (uses environment variables or defaults)
app = create_app()

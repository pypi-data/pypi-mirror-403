"""
Server configuration for the Analytic Continuation Server.

This module provides:
- ServerConfig: Pydantic model for server configuration
- load_config_from_env(): Load configuration from environment variables
"""

import os
from typing import Optional

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """
    Configuration for the Analytic Continuation Server.

    Attributes
    ----------
    cors_origins : list[str]
        List of allowed CORS origins. Default is ["*"] which allows all origins.
    enable_domaincolor : bool
        Enable domain coloring endpoints. Default True.
        Set to False to disable even if py-domaincolor is installed.
    enable_laurent : bool
        Enable Laurent series fitting endpoints. Default True.
    log_level : str
        Logging level for the server. Default "info".
    title : str
        API title for OpenAPI docs.
    description : str
        API description for OpenAPI docs.
    version : str
        API version.
    debug : bool
        Enable debug mode.

    Examples
    --------
    >>> config = ServerConfig(cors_origins=["https://myapp.com"])
    >>> config.enable_domaincolor
    True

    >>> config = ServerConfig(enable_domaincolor=False, log_level="debug")
    >>> config.log_level
    'debug'
    """

    cors_origins: list[str] = Field(
        default=["*"],
        description="List of allowed CORS origins",
    )
    enable_domaincolor: bool = Field(
        default=True,
        description="Enable domain coloring endpoints",
    )
    enable_laurent: bool = Field(
        default=True,
        description="Enable Laurent series fitting endpoints",
    )
    log_level: str = Field(
        default="info",
        description="Logging level (debug, info, warning, error, critical)",
    )
    title: str = Field(
        default="Analytic Continuation Server",
        description="API title for OpenAPI docs",
    )
    description: str = Field(
        default="API for domain coloring visualization, coordinate transforms, and analytic continuation",
        description="API description for OpenAPI docs",
    )
    version: str = Field(
        default="0.1.0",
        description="API version",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    model_config = {"extra": "ignore"}


def load_config_from_env() -> ServerConfig:
    """
    Load server configuration from environment variables.

    Environment Variables
    ---------------------
    ACS_CORS_ORIGINS : str
        Comma-separated list of allowed CORS origins.
        Default: "*"
    ACS_ENABLE_DOMAINCOLOR : str
        Enable domain coloring endpoints ("true"/"false").
        Default: "true"
    ACS_ENABLE_LAURENT : str
        Enable Laurent series fitting endpoints ("true"/"false").
        Default: "true"
    ACS_LOG_LEVEL : str
        Logging level.
        Default: "info"
    ACS_TITLE : str
        API title for OpenAPI docs.
    ACS_DESCRIPTION : str
        API description for OpenAPI docs.
    ACS_VERSION : str
        API version.
    ACS_DEBUG : str
        Enable debug mode ("true"/"false").
        Default: "false"

    Returns
    -------
    ServerConfig
        Configuration loaded from environment variables.

    Examples
    --------
    >>> import os
    >>> os.environ["ACS_CORS_ORIGINS"] = "https://example.com,https://api.example.com"
    >>> os.environ["ACS_ENABLE_DOMAINCOLOR"] = "false"
    >>> config = load_config_from_env()
    >>> config.cors_origins
    ['https://example.com', 'https://api.example.com']
    >>> config.enable_domaincolor
    False
    """

    def parse_bool(value: Optional[str], default: bool = True) -> bool:
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def parse_list(value: Optional[str], default: list[str]) -> list[str]:
        if value is None:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]

    cors_origins = parse_list(os.environ.get("ACS_CORS_ORIGINS"), ["*"])
    enable_domaincolor = parse_bool(os.environ.get("ACS_ENABLE_DOMAINCOLOR"), True)
    enable_laurent = parse_bool(os.environ.get("ACS_ENABLE_LAURENT"), True)
    log_level = os.environ.get("ACS_LOG_LEVEL", "info")
    title = os.environ.get("ACS_TITLE", "Analytic Continuation Server")
    description = os.environ.get(
        "ACS_DESCRIPTION",
        "API for domain coloring visualization, coordinate transforms, and analytic continuation",
    )
    version = os.environ.get("ACS_VERSION", "0.1.0")
    debug = parse_bool(os.environ.get("ACS_DEBUG"), False)

    return ServerConfig(
        cors_origins=cors_origins,
        enable_domaincolor=enable_domaincolor,
        enable_laurent=enable_laurent,
        log_level=log_level,
        title=title,
        description=description,
        version=version,
        debug=debug,
    )

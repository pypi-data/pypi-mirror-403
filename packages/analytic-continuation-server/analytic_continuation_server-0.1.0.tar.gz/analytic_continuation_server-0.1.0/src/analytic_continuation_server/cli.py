"""
CLI entry point for the Analytic Continuation Server.

Provides the `serve-analytic-continuation` command.

Usage
-----
Basic usage:

    serve-analytic-continuation --port 8000

With custom CORS:

    serve-analytic-continuation --cors-origin https://myapp.com --cors-origin https://api.myapp.com

Disable optional features:

    serve-analytic-continuation --disable-domaincolor

Using a config file:

    serve-analytic-continuation --config /path/to/config.json
"""

import argparse
import json
import sys
from typing import Optional


def load_config_file(path: str) -> dict:
    """Load configuration from a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def main(args: Optional[list[str]] = None):
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Run the Analytic Continuation Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default="info",
        help="Log level",
    )
    parser.add_argument(
        "--cors-origin",
        dest="cors_origins",
        action="append",
        help="Allowed CORS origin (can be specified multiple times). "
        "Default: allow all origins (*)",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        help="Path to JSON configuration file",
    )
    parser.add_argument(
        "--disable-domaincolor",
        action="store_true",
        help="Disable domain coloring endpoints",
    )
    parser.add_argument(
        "--disable-laurent",
        action="store_true",
        help="Disable Laurent series fitting endpoints",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    parser.add_argument(
        "--title",
        help="API title for OpenAPI docs",
    )
    parser.add_argument(
        "--version-tag",
        dest="version",
        help="API version tag",
    )

    parsed = parser.parse_args(args)

    try:
        import uvicorn
    except ImportError:
        print(
            "Error: uvicorn is required but not installed. "
            "Install with: pip install uvicorn[standard]",
            file=sys.stderr,
        )
        sys.exit(1)

    # Build configuration from CLI args and config file
    from .config import ServerConfig

    config_dict: dict = {}

    # Load from config file first (if specified)
    if parsed.config:
        try:
            config_dict = load_config_file(parsed.config)
        except FileNotFoundError:
            print(f"Error: Config file not found: {parsed.config}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file: {e}", file=sys.stderr)
            sys.exit(1)

    # Override with CLI arguments (CLI takes precedence)
    if parsed.cors_origins:
        config_dict["cors_origins"] = parsed.cors_origins
    elif "cors_origins" not in config_dict:
        config_dict["cors_origins"] = ["*"]

    if parsed.disable_domaincolor:
        config_dict["enable_domaincolor"] = False
    elif "enable_domaincolor" not in config_dict:
        config_dict["enable_domaincolor"] = True

    if parsed.disable_laurent:
        config_dict["enable_laurent"] = False
    elif "enable_laurent" not in config_dict:
        config_dict["enable_laurent"] = True

    config_dict["log_level"] = parsed.log_level

    if parsed.debug:
        config_dict["debug"] = True

    if parsed.title:
        config_dict["title"] = parsed.title

    if parsed.version:
        config_dict["version"] = parsed.version

    # Validate configuration
    try:
        config = ServerConfig(**config_dict)
    except Exception as e:
        print(f"Error: Invalid configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Create app with configuration for factory function reference
    # Store config in a module-level variable for the factory
    import analytic_continuation_server.cli as cli_module

    cli_module._cli_config = config

    print(f"Starting Analytic Continuation Server on {parsed.host}:{parsed.port}")
    print(f"  Documentation: http://{parsed.host}:{parsed.port}/docs")
    print(f"  Health check: http://{parsed.host}:{parsed.port}/api/health")

    if not config.enable_domaincolor:
        print("  Domain coloring endpoints: DISABLED")
    if not config.enable_laurent:
        print("  Laurent fitting endpoints: DISABLED")
    if config.debug:
        print("  Debug mode: ENABLED")

    # When using reload, uvicorn needs a string reference
    # For custom config, we need to use factory mode
    if parsed.reload or parsed.workers > 1:
        # Use factory string for reload/workers mode
        uvicorn.run(
            "analytic_continuation_server.cli:_create_app_from_cli",
            host=parsed.host,
            port=parsed.port,
            reload=parsed.reload,
            workers=parsed.workers if not parsed.reload else 1,
            log_level=parsed.log_level,
            factory=True,
        )
    else:
        # Direct app creation for single-worker mode
        from .app import create_app

        app = create_app(config)
        uvicorn.run(
            app,
            host=parsed.host,
            port=parsed.port,
            log_level=parsed.log_level,
        )


# Module-level config storage for factory mode
_cli_config: Optional["ServerConfig"] = None  # type: ignore


def _create_app_from_cli():
    """Factory function for uvicorn when using reload/workers mode."""
    from .app import create_app
    from .config import ServerConfig

    global _cli_config

    if _cli_config is not None:
        return create_app(_cli_config)
    else:
        # Fallback to default config
        return create_app()


if __name__ == "__main__":
    main()

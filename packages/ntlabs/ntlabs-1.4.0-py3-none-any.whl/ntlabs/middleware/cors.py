"""
CORS configuration utilities for FastAPI.

Provides pre-configured CORS settings for common scenarios.
"""

import logging

logger = logging.getLogger(__name__)


def setup_cors(
    app,
    origins: str | list[str] | None = None,
    allow_credentials: bool = True,
    allow_methods: list[str] | None = None,
    allow_headers: list[str] | None = None,
    expose_headers: list[str] | None = None,
    max_age: int = 600,
    development_mode: bool = False,
):
    """
    Configure CORS for FastAPI application.

    Args:
        app: FastAPI application
        origins: Allowed origins (URL or list of URLs)
        allow_credentials: Allow credentials (cookies, auth headers)
        allow_methods: Allowed HTTP methods
        allow_headers: Allowed request headers
        expose_headers: Headers exposed to browser
        max_age: Preflight cache max age in seconds
        development_mode: If True, allows all origins

    Example:
        from fastapi import FastAPI
        from ntlabs.middleware import setup_cors

        app = FastAPI()

        # Production
        setup_cors(
            app,
            origins=[
                "https://app.neuralthinkers.com",
                "https://neuralthinkers.com",
            ],
        )

        # Development
        setup_cors(app, development_mode=True)
    """
    try:
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as err:
        raise ImportError(
            "fastapi is required for CORS middleware. "
            "Install it with: pip install fastapi"
        ) from err

    # Determine origins
    if development_mode:
        allowed_origins = ["*"]
    elif origins:
        if isinstance(origins, str):
            allowed_origins = [origins]
        else:
            allowed_origins = list(origins)
    else:
        allowed_origins = []

    # Default methods
    if allow_methods is None:
        allow_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

    # Default headers
    if allow_headers is None:
        allow_headers = [
            "Accept",
            "Accept-Language",
            "Content-Type",
            "Authorization",
            "X-API-Key",
            "X-Request-ID",
            "X-Forwarded-For",
            "X-Forwarded-Proto",
        ]

    # Default expose headers
    if expose_headers is None:
        expose_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
            "X-Request-ID",
        ]

    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=allow_methods,
        allow_headers=allow_headers,
        expose_headers=expose_headers,
        max_age=max_age,
    )

    logger.info(
        f"CORS configured: origins={allowed_origins}, "
        f"credentials={allow_credentials}"
    )


def get_cors_origins_from_env(
    env_var: str = "CORS_ORIGINS",
    default: list[str] | None = None,
) -> list[str]:
    """
    Get CORS origins from environment variable.

    Args:
        env_var: Environment variable name
        default: Default origins if env var not set

    Returns:
        List of allowed origins

    Example:
        # CORS_ORIGINS="https://app.example.com,https://admin.example.com"
        origins = get_cors_origins_from_env()
    """
    import os

    value = os.getenv(env_var, "")

    if not value:
        return default or []

    return [origin.strip() for origin in value.split(",") if origin.strip()]


# Pre-configured CORS settings
class CORSPresets:
    """Pre-configured CORS settings for common scenarios."""

    @staticmethod
    def development(app):
        """Allow all origins for development."""
        setup_cors(app, development_mode=True)

    @staticmethod
    def production_single_origin(app, origin: str):
        """Single origin production setup."""
        setup_cors(
            app,
            origins=[origin],
            allow_credentials=True,
        )

    @staticmethod
    def api_gateway(app, origins: list[str]):
        """API gateway setup with multiple frontends."""
        setup_cors(
            app,
            origins=origins,
            allow_credentials=True,
            expose_headers=[
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
                "X-Request-ID",
                "X-Total-Count",
                "Link",
            ],
        )

    @staticmethod
    def public_api(app):
        """Public API with no credentials."""
        setup_cors(
            app,
            origins=["*"],
            allow_credentials=False,
            allow_methods=["GET", "POST"],
        )

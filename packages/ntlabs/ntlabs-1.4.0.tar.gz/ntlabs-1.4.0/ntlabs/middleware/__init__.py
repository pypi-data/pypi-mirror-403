"""
NTLabs Middleware - FastAPI middleware utilities.

This module provides middleware for FastAPI applications:
- Rate limiting with Redis
- CORS configuration
- Security headers
- Request logging

Quick Start:
    from fastapi import FastAPI
    from ntlabs.middleware import (
        RateLimitMiddleware,
        SecurityHeadersMiddleware,
        LoggingMiddleware,
        setup_cors,
    )

    app = FastAPI()

    # Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        redis_url="redis://localhost:6379",
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Request logging
    app.add_middleware(LoggingMiddleware)

    # CORS
    setup_cors(app, origins=["https://myapp.com"])

Using Presets:
    from ntlabs.middleware import CORSPresets, SecurityPresets

    # Development mode
    CORSPresets.development(app)
    SecurityPresets.development(app)

    # Production
    CORSPresets.api_gateway(app, origins=["https://app.example.com"])
    SecurityPresets.api(app)
"""

from .cors import (
    CORSPresets,
    get_cors_origins_from_env,
    setup_cors,
)
from .logging import (
    LoggingMiddleware,
    StructuredLogger,
    get_request_id,
)
from .rate_limiting import (
    DEFAULT_TIER_CONFIG,
    EndpointConfig,
    RateLimitMiddleware,
    RateLimitTier,
    TierConfig,
    rate_limit,
)
from .security import (
    SecurityHeadersMiddleware,
    SecurityPresets,
    get_default_csp,
)

__all__ = [
    # Rate Limiting
    "RateLimitMiddleware",
    "RateLimitTier",
    "TierConfig",
    "EndpointConfig",
    "DEFAULT_TIER_CONFIG",
    "rate_limit",
    # CORS
    "setup_cors",
    "get_cors_origins_from_env",
    "CORSPresets",
    # Security
    "SecurityHeadersMiddleware",
    "get_default_csp",
    "SecurityPresets",
    # Logging
    "LoggingMiddleware",
    "StructuredLogger",
    "get_request_id",
]

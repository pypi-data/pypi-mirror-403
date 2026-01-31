"""
Error response schemas.

Standard error response formats for API consistency.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """
    Detailed error information.

    Used for validation errors and complex error scenarios.
    """

    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: str | None = Field(None, description="Error code")
    context: dict[str, Any] | None = Field(None, description="Additional context")

    model_config = {
        "json_schema_extra": {
            "example": {
                "field": "email",
                "message": "Invalid email format",
                "code": "invalid_format",
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Standard error response.

    All API errors should follow this format for consistency.

    Example:
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            return JSONResponse(
                status_code=exc.status_code,
                content=ErrorResponse(
                    error=exc.detail,
                    code="http_error",
                    status_code=exc.status_code,
                ).model_dump()
            )
    """

    error: str = Field(..., description="Error message")
    code: str = Field(default="error", description="Error code")
    status_code: int = Field(default=400, description="HTTP status code")
    details: list[ErrorDetail] | None = Field(None, description="Error details")
    request_id: str | None = Field(None, description="Request ID for tracking")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    documentation_url: str | None = Field(
        None, description="Link to error documentation"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Validation failed",
                "code": "validation_error",
                "status_code": 422,
                "details": [{"field": "email", "message": "Invalid email format"}],
                "request_id": "req_abc123",
                "timestamp": "2026-01-27T12:00:00Z",
            }
        }
    }


class ValidationErrorResponse(ErrorResponse):
    """
    Validation error response.

    Specialized error response for request validation failures.
    """

    error: str = Field(default="Validation Error", description="Error message")
    code: str = Field(default="validation_error", description="Error code")
    status_code: int = Field(default=422, description="HTTP status code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Validation Error",
                "code": "validation_error",
                "status_code": 422,
                "details": [
                    {
                        "field": "cpf",
                        "message": "Invalid CPF format",
                        "code": "invalid_cpf",
                    },
                    {
                        "field": "email",
                        "message": "Email is required",
                        "code": "required",
                    },
                ],
            }
        }
    }


class NotFoundErrorResponse(ErrorResponse):
    """Resource not found error response."""

    error: str = Field(default="Resource not found", description="Error message")
    code: str = Field(default="not_found", description="Error code")
    status_code: int = Field(default=404, description="HTTP status code")
    resource_type: str | None = Field(None, description="Type of resource not found")
    resource_id: str | None = Field(None, description="ID of resource not found")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "User not found",
                "code": "not_found",
                "status_code": 404,
                "resource_type": "user",
                "resource_id": "user_123",
            }
        }
    }


class UnauthorizedErrorResponse(ErrorResponse):
    """Authentication error response."""

    error: str = Field(default="Unauthorized", description="Error message")
    code: str = Field(default="unauthorized", description="Error code")
    status_code: int = Field(default=401, description="HTTP status code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Invalid or expired token",
                "code": "unauthorized",
                "status_code": 401,
            }
        }
    }


class ForbiddenErrorResponse(ErrorResponse):
    """Authorization error response."""

    error: str = Field(default="Forbidden", description="Error message")
    code: str = Field(default="forbidden", description="Error code")
    status_code: int = Field(default=403, description="HTTP status code")
    required_permission: str | None = Field(None, description="Permission required")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "You don't have permission to access this resource",
                "code": "forbidden",
                "status_code": 403,
                "required_permission": "admin:read",
            }
        }
    }


class RateLimitErrorResponse(ErrorResponse):
    """Rate limit exceeded error response."""

    error: str = Field(default="Rate limit exceeded", description="Error message")
    code: str = Field(default="rate_limit_exceeded", description="Error code")
    status_code: int = Field(default=429, description="HTTP status code")
    retry_after: int | None = Field(None, description="Seconds until retry is allowed")
    limit: int | None = Field(None, description="Rate limit")
    remaining: int | None = Field(None, description="Remaining requests")
    reset_at: datetime | None = Field(None, description="When limit resets")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Rate limit exceeded. Please try again later.",
                "code": "rate_limit_exceeded",
                "status_code": 429,
                "retry_after": 60,
                "limit": 100,
                "remaining": 0,
                "reset_at": "2026-01-27T12:01:00Z",
            }
        }
    }


class InternalErrorResponse(ErrorResponse):
    """Internal server error response."""

    error: str = Field(default="Internal server error", description="Error message")
    code: str = Field(default="internal_error", description="Error code")
    status_code: int = Field(default=500, description="HTTP status code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "An unexpected error occurred",
                "code": "internal_error",
                "status_code": 500,
                "request_id": "req_abc123",
            }
        }
    }


class ServiceUnavailableErrorResponse(ErrorResponse):
    """Service unavailable error response."""

    error: str = Field(
        default="Service temporarily unavailable", description="Error message"
    )
    code: str = Field(default="service_unavailable", description="Error code")
    status_code: int = Field(default=503, description="HTTP status code")
    retry_after: int | None = Field(
        None, description="Seconds until service is available"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "Service is temporarily unavailable for maintenance",
                "code": "service_unavailable",
                "status_code": 503,
                "retry_after": 300,
            }
        }
    }


# Error code constants
class ErrorCodes:
    """Standard error codes."""

    # Validation
    VALIDATION_ERROR = "validation_error"
    INVALID_FORMAT = "invalid_format"
    REQUIRED_FIELD = "required"
    INVALID_VALUE = "invalid_value"

    # Authentication
    UNAUTHORIZED = "unauthorized"
    INVALID_TOKEN = "invalid_token"
    EXPIRED_TOKEN = "expired_token"
    INVALID_CREDENTIALS = "invalid_credentials"

    # Authorization
    FORBIDDEN = "forbidden"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"

    # Resources
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    CONFLICT = "conflict"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Server
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    EXTERNAL_SERVICE_ERROR = "external_service_error"

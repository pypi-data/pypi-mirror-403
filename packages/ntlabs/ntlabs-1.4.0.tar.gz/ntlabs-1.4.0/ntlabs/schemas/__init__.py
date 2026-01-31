"""
NTLabs Schemas - Pydantic schemas for API responses.

This module provides standard Pydantic schemas for:
- Authentication responses (tokens, users)
- Pagination
- Error responses
- Common patterns

Quick Start:
    from ntlabs.schemas import (
        TokenResponse,
        UserResponse,
        PaginatedResponse,
        ErrorResponse,
    )

    @router.post("/auth/token", response_model=TokenResponse)
    async def get_token():
        return TokenResponse(
            access_token="xxx",
            expires_in=3600,
        )

    @router.get("/users", response_model=PaginatedResponse[UserResponse])
    async def list_users(page: int = 1):
        users = await get_users(page)
        return PaginatedResponse(
            items=users,
            total=100,
            page=page,
            page_size=20,
        )

Error Handling:
    from ntlabs.schemas import ErrorResponse, ValidationErrorResponse

    @app.exception_handler(HTTPException)
    async def handle_http_error(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.detail,
                status_code=exc.status_code,
            ).model_dump(),
        )
"""

from .auth import (
    OAuthCallbackRequest,
    OAuthUrlResponse,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    SessionInfo,
    TokenResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from .common import (
    Address,
    BulkOperationResponse,
    ContactInfo,
    CountResponse,
    DataResponse,
    FileUploadResponse,
    HealthResponse,
    IdResponse,
    MetadataMixin,
    SoftDeleteMixin,
    SuccessResponse,
    TimestampMixin,
    WebhookPayload,
)
from .errors import (
    ErrorCodes,
    ErrorDetail,
    ErrorResponse,
    ForbiddenErrorResponse,
    InternalErrorResponse,
    NotFoundErrorResponse,
    RateLimitErrorResponse,
    ServiceUnavailableErrorResponse,
    UnauthorizedErrorResponse,
    ValidationErrorResponse,
)
from .pagination import (
    CursorPaginatedResponse,
    CursorPaginationParams,
    PaginatedResponse,
    PaginatedResponseWithMeta,
    PaginationParams,
    paginate_list,
)

__all__ = [
    # Auth
    "TokenResponse",
    "RefreshTokenRequest",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "PasswordChangeRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "OAuthUrlResponse",
    "OAuthCallbackRequest",
    "SessionInfo",
    # Pagination
    "PaginationParams",
    "PaginatedResponse",
    "PaginatedResponseWithMeta",
    "CursorPaginationParams",
    "CursorPaginatedResponse",
    "paginate_list",
    # Errors
    "ErrorDetail",
    "ErrorResponse",
    "ValidationErrorResponse",
    "NotFoundErrorResponse",
    "UnauthorizedErrorResponse",
    "ForbiddenErrorResponse",
    "RateLimitErrorResponse",
    "InternalErrorResponse",
    "ServiceUnavailableErrorResponse",
    "ErrorCodes",
    # Common
    "TimestampMixin",
    "SoftDeleteMixin",
    "MetadataMixin",
    "HealthResponse",
    "SuccessResponse",
    "DataResponse",
    "CountResponse",
    "IdResponse",
    "BulkOperationResponse",
    "FileUploadResponse",
    "WebhookPayload",
    "Address",
    "ContactInfo",
]

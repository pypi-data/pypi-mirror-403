"""
Authentication-related schemas.

Standard schemas for authentication responses.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenResponse(BaseModel):
    """
    OAuth2/JWT token response.

    Example:
        @router.post("/auth/token", response_model=TokenResponse)
        async def get_token(credentials: Credentials):
            return TokenResponse(
                access_token="xxx",
                refresh_token="yyy",
                expires_in=3600,
            )
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str | None = Field(None, description="Refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    scope: str | None = Field(None, description="Token scopes")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "read write",
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Request to refresh an access token."""

    refresh_token: str = Field(..., description="Refresh token")

    model_config = {
        "json_schema_extra": {
            "example": {"refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4..."}
        }
    }


class UserResponse(BaseModel):
    """
    User profile response.

    Standard user representation for API responses.
    """

    id: str = Field(..., description="User ID")
    email: EmailStr | None = Field(None, description="User email")
    name: str | None = Field(None, description="User display name")
    avatar_url: str | None = Field(None, description="Avatar URL")
    role: str = Field(default="user", description="User role")
    is_active: bool = Field(default=True, description="Account active status")
    is_verified: bool = Field(default=False, description="Email verified status")
    created_at: datetime | None = Field(None, description="Account creation date")
    updated_at: datetime | None = Field(None, description="Last update date")
    metadata: dict | None = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "user_123abc",
                "email": "user@example.com",
                "name": "John Doe",
                "avatar_url": "https://example.com/avatar.jpg",
                "role": "user",
                "is_active": True,
                "is_verified": True,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-27T12:00:00Z",
            }
        }
    }


class UserCreate(BaseModel):
    """Request to create a new user."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="Password")
    name: str | None = Field(None, description="Display name")
    metadata: dict | None = Field(default_factory=dict, description="Additional data")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User",
            }
        }
    }


class UserUpdate(BaseModel):
    """Request to update user profile."""

    name: str | None = Field(None, description="Display name")
    avatar_url: str | None = Field(None, description="Avatar URL")
    metadata: dict | None = Field(None, description="Additional data")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Updated Name",
                "avatar_url": "https://example.com/new-avatar.jpg",
            }
        }
    }


class PasswordChangeRequest(BaseModel):
    """Request to change password."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePass456!",
            }
        }
    }


class PasswordResetRequest(BaseModel):
    """Request to initiate password reset."""

    email: EmailStr = Field(..., description="User email")

    model_config = {"json_schema_extra": {"example": {"email": "user@example.com"}}}


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "reset_token_here",
                "new_password": "NewSecurePass456!",
            }
        }
    }


class OAuthUrlResponse(BaseModel):
    """OAuth authorization URL response."""

    url: str = Field(..., description="Authorization URL")
    state: str | None = Field(None, description="State parameter")
    provider: str = Field(..., description="OAuth provider name")

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://accounts.google.com/o/oauth2/auth?...",
                "state": "random_state_string",
                "provider": "google",
            }
        }
    }


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request."""

    code: str = Field(..., description="Authorization code")
    state: str | None = Field(None, description="State parameter")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code": "authorization_code_here",
                "state": "random_state_string",
            }
        }
    }


class SessionInfo(BaseModel):
    """Current session information."""

    user: UserResponse = Field(..., description="Current user")
    expires_at: datetime = Field(..., description="Session expiry")
    permissions: list[str] = Field(default_factory=list, description="User permissions")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user": {
                    "id": "user_123",
                    "email": "user@example.com",
                    "name": "John Doe",
                },
                "expires_at": "2026-01-27T14:00:00Z",
                "permissions": ["read:users", "write:own"],
            }
        }
    }

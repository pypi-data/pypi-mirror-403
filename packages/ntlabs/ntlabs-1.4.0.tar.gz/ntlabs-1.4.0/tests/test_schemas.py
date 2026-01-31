"""
Tests for ntlabs.schemas module.

Tests Pydantic schemas for API responses.
"""

from datetime import datetime

import pytest

from ntlabs.schemas import (
    Address,
    CountResponse,
    CursorPaginatedResponse,
    DataResponse,
    ErrorCodes,
    ErrorDetail,
    # Errors
    ErrorResponse,
    # Common
    HealthResponse,
    PaginatedResponse,
    PaginatedResponseWithMeta,
    # Pagination
    PaginationParams,
    PasswordChangeRequest,
    SuccessResponse,
    # Auth
    TokenResponse,
    UserCreate,
    UserResponse,
    ValidationErrorResponse,
    paginate_list,
)

# =============================================================================
# Auth Schema Tests
# =============================================================================


class TestAuthSchemas:
    """Tests for authentication schemas."""

    def test_token_response(self):
        """Test TokenResponse schema."""
        token = TokenResponse(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            expires_in=3600,
        )
        assert token.access_token.startswith("eyJ")
        assert token.expires_in == 3600
        assert token.token_type == "Bearer"

    def test_token_response_with_refresh(self):
        """Test TokenResponse with refresh token."""
        token = TokenResponse(
            access_token="access_token",
            refresh_token="refresh_token",
            expires_in=3600,
            scope="read write",
        )
        assert token.refresh_token == "refresh_token"
        assert token.scope == "read write"

    def test_user_response(self):
        """Test UserResponse schema."""
        user = UserResponse(
            id="user_123",
            email="user@example.com",
            name="John Doe",
            role="user",
        )
        assert user.id == "user_123"
        assert user.email == "user@example.com"
        assert user.is_active is True  # Default

    def test_user_response_with_timestamps(self):
        """Test UserResponse with timestamps."""
        now = datetime.utcnow()
        user = UserResponse(
            id="user_123",
            created_at=now,
            updated_at=now,
        )
        assert user.created_at == now

    def test_user_create_validation(self):
        """Test UserCreate validation."""
        user = UserCreate(
            email="user@example.com",
            password="SecurePass123!",
            name="John Doe",
        )
        assert user.email == "user@example.com"

    def test_user_create_short_password(self):
        """Test UserCreate rejects short password."""
        with pytest.raises(ValueError):
            UserCreate(
                email="user@example.com",
                password="short",  # Less than 8 chars
            )

    def test_password_change_request(self):
        """Test PasswordChangeRequest schema."""
        request = PasswordChangeRequest(
            current_password="OldPass123!",
            new_password="NewPass456!",
        )
        assert request.current_password == "OldPass123!"


# =============================================================================
# Pagination Schema Tests
# =============================================================================


class TestPaginationSchemas:
    """Tests for pagination schemas."""

    def test_pagination_params_defaults(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20
        assert params.offset == 0
        assert params.limit == 20

    def test_pagination_params_custom(self):
        """Test custom pagination parameters."""
        params = PaginationParams(page=3, page_size=50)
        assert params.offset == 100  # (3-1) * 50
        assert params.limit == 50

    def test_pagination_params_validation(self):
        """Test pagination validation."""
        with pytest.raises(ValueError):
            PaginationParams(page=0)  # Must be >= 1

        with pytest.raises(ValueError):
            PaginationParams(page_size=200)  # Max 100

    def test_paginated_response(self):
        """Test PaginatedResponse schema."""
        response = PaginatedResponse(
            items=[{"id": "1"}, {"id": "2"}],
            total=50,
            page=1,
            page_size=20,
        )
        assert len(response.items) == 2
        assert response.total == 50
        assert response.total_pages == 3
        assert response.has_next is True
        assert response.has_prev is False

    def test_paginated_response_last_page(self):
        """Test PaginatedResponse on last page."""
        response = PaginatedResponse(
            items=[{"id": "1"}],
            total=41,
            page=3,
            page_size=20,
        )
        assert response.total_pages == 3
        assert response.has_next is False
        assert response.has_prev is True

    def test_paginated_response_with_meta(self):
        """Test PaginatedResponseWithMeta schema."""
        response = PaginatedResponseWithMeta(
            items=[{"id": "1"}],
            total=50,
            page=2,
            page_size=20,
        )
        assert response.total_pages == 3
        assert response.has_next is True
        assert response.has_prev is True
        assert response.next_page == 3
        assert response.prev_page == 1

    def test_cursor_paginated_response(self):
        """Test CursorPaginatedResponse schema."""
        response = CursorPaginatedResponse(
            items=[{"id": "1"}, {"id": "2"}],
            next_cursor="eyJpZCI6IjIifQ==",
            has_more=True,
        )
        assert response.next_cursor is not None
        assert response.has_more is True

    def test_paginate_list_helper(self):
        """Test paginate_list helper function."""
        items = [{"id": str(i)} for i in range(20)]
        response = paginate_list(items, total=100, page=1, page_size=20)

        assert len(response.items) == 20
        assert response.total == 100


# =============================================================================
# Error Schema Tests
# =============================================================================


class TestErrorSchemas:
    """Tests for error schemas."""

    def test_error_response(self):
        """Test basic ErrorResponse."""
        error = ErrorResponse(
            error="Something went wrong",
            code="internal_error",
            status_code=500,
        )
        assert error.error == "Something went wrong"
        assert error.code == "internal_error"
        assert error.timestamp is not None

    def test_error_response_with_details(self):
        """Test ErrorResponse with details."""
        error = ErrorResponse(
            error="Validation failed",
            code="validation_error",
            status_code=422,
            details=[
                ErrorDetail(
                    field="email", message="Invalid email", code="invalid_format"
                ),
                ErrorDetail(field="age", message="Must be positive"),
            ],
            request_id="req_abc123",
        )
        assert len(error.details) == 2
        assert error.details[0].field == "email"

    def test_validation_error_response(self):
        """Test ValidationErrorResponse defaults."""
        error = ValidationErrorResponse(
            details=[ErrorDetail(field="name", message="Required")],
        )
        assert error.code == "validation_error"
        assert error.status_code == 422

    def test_error_codes(self):
        """Test ErrorCodes constants."""
        assert ErrorCodes.VALIDATION_ERROR == "validation_error"
        assert ErrorCodes.UNAUTHORIZED == "unauthorized"
        assert ErrorCodes.NOT_FOUND == "not_found"
        assert ErrorCodes.RATE_LIMIT_EXCEEDED == "rate_limit_exceeded"


# =============================================================================
# Common Schema Tests
# =============================================================================


class TestCommonSchemas:
    """Tests for common schemas."""

    def test_health_response(self):
        """Test HealthResponse schema."""
        health = HealthResponse(
            status="healthy",
            version="1.0.0",
            checks={
                "database": {"status": "healthy"},
                "redis": {"status": "healthy"},
            },
        )
        assert health.status == "healthy"
        assert health.version == "1.0.0"

    def test_success_response(self):
        """Test SuccessResponse schema."""
        response = SuccessResponse(message="User deleted")
        assert response.success is True
        assert response.message == "User deleted"

    def test_success_response_defaults(self):
        """Test SuccessResponse defaults."""
        response = SuccessResponse()
        assert response.success is True
        assert response.message == "Operation completed successfully"

    def test_data_response(self):
        """Test DataResponse wrapper."""
        response = DataResponse(
            data={"id": "123", "name": "Test"},
            message="Data retrieved",
        )
        assert response.data["id"] == "123"

    def test_count_response(self):
        """Test CountResponse schema."""
        response = CountResponse(count=42)
        assert response.count == 42

    def test_count_response_validation(self):
        """Test CountResponse validation."""
        with pytest.raises(ValueError):
            CountResponse(count=-1)  # Must be >= 0

    def test_address_schema(self):
        """Test Address schema."""
        address = Address(
            street="Av. Paulista",
            number="1000",
            city="São Paulo",
            state="SP",
            postal_code="01310-100",
        )
        assert address.street == "Av. Paulista"
        assert address.country == "BR"  # Default

    def test_address_state_validation(self):
        """Test Address state code validation."""
        # Should work with 2-char state
        address = Address(
            street="Rua Teste",
            city="Test City",
            state="MG",
            postal_code="30000-000",
        )
        assert address.state == "MG"


# =============================================================================
# Schema Serialization Tests
# =============================================================================


class TestSchemaSerialization:
    """Tests for schema serialization."""

    def test_token_response_json(self):
        """Test TokenResponse JSON serialization."""
        token = TokenResponse(
            access_token="test_token",
            expires_in=3600,
        )
        json_data = token.model_dump()
        assert "access_token" in json_data
        assert json_data["token_type"] == "Bearer"

    def test_user_response_exclude_none(self):
        """Test UserResponse serialization excluding None."""
        user = UserResponse(id="123")
        json_data = user.model_dump(exclude_none=True)
        assert "email" not in json_data

    def test_error_response_json(self):
        """Test ErrorResponse JSON serialization."""
        error = ErrorResponse(
            error="Test error",
            code="test",
            status_code=400,
        )
        json_data = error.model_dump()
        assert json_data["error"] == "Test error"
        assert "timestamp" in json_data

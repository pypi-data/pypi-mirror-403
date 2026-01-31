"""
NTLabs SDK - Exception Tests
Tests for all SDK exception classes.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest

from ntlabs.exceptions import (
    APIError,
    AuthenticationError,
    InsufficientCreditsError,
    NTLError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)


class TestNTLError:
    """Tests for base NTLError."""

    def test_basic_initialization(self):
        """Exception initializes with message."""
        error = NTLError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None
        assert error.response == {}

    def test_with_status_code(self):
        """Exception stores status code."""
        error = NTLError("Test error", status_code=500)
        assert error.status_code == 500

    def test_with_response(self):
        """Exception stores response dict."""
        response = {"detail": "Error details", "code": "ERROR_001"}
        error = NTLError("Test error", response=response)
        assert error.response == response
        assert error.response["detail"] == "Error details"

    def test_all_parameters(self):
        """Exception stores all parameters."""
        response = {"errors": ["Error 1", "Error 2"]}
        error = NTLError("Full error", status_code=400, response=response)
        assert error.message == "Full error"
        assert error.status_code == 400
        assert error.response == response


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_inheritance(self):
        """AuthenticationError inherits from NTLError."""
        error = AuthenticationError("Invalid API key")
        assert isinstance(error, NTLError)
        assert isinstance(error, Exception)

    def test_typical_usage(self):
        """Typical authentication error usage."""
        error = AuthenticationError(
            "API key required",
            status_code=401,
            response={"detail": "Missing X-API-Key header"},
        )
        assert error.status_code == 401
        assert "Missing X-API-Key" in error.response["detail"]


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_inheritance(self):
        """RateLimitError inherits from NTLError."""
        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, NTLError)

    def test_retry_after(self):
        """RateLimitError stores retry_after."""
        error = RateLimitError("Rate limit exceeded", retry_after=30)
        assert error.retry_after == 30

    def test_with_all_parameters(self):
        """RateLimitError with all parameters."""
        error = RateLimitError(
            "Too many requests",
            retry_after=60,
            status_code=429,
            response={"detail": "Rate limit exceeded"},
        )
        assert error.message == "Too many requests"
        assert error.retry_after == 60
        assert error.status_code == 429

    def test_retry_after_none(self):
        """RateLimitError without retry_after."""
        error = RateLimitError("Rate limit exceeded")
        assert error.retry_after is None


class TestInsufficientCreditsError:
    """Tests for InsufficientCreditsError."""

    def test_inheritance(self):
        """InsufficientCreditsError inherits from NTLError."""
        error = InsufficientCreditsError("Not enough credits")
        assert isinstance(error, NTLError)

    def test_typical_usage(self):
        """Typical insufficient credits error."""
        error = InsufficientCreditsError(
            "Not enough credits for this operation",
            status_code=402,
            response={"required": 10.0, "available": 5.0},
        )
        assert error.status_code == 402
        assert error.response["required"] == 10.0


class TestAPIError:
    """Tests for APIError."""

    def test_inheritance(self):
        """APIError inherits from NTLError."""
        error = APIError("Internal server error")
        assert isinstance(error, NTLError)

    def test_typical_usage(self):
        """Typical API error."""
        error = APIError(
            "Internal server error",
            status_code=500,
            response={"detail": "Database connection failed"},
        )
        assert error.status_code == 500


class TestValidationError:
    """Tests for ValidationError."""

    def test_inheritance(self):
        """ValidationError inherits from NTLError."""
        error = ValidationError("Invalid input")
        assert isinstance(error, NTLError)

    def test_typical_usage(self):
        """Typical validation error."""
        error = ValidationError(
            "Validation failed",
            status_code=422,
            response={
                "detail": [{"loc": ["body", "email"], "msg": "invalid email format"}]
            },
        )
        assert error.status_code == 422


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError."""

    def test_inheritance(self):
        """ServiceUnavailableError inherits from NTLError."""
        error = ServiceUnavailableError("Service unavailable")
        assert isinstance(error, NTLError)

    def test_typical_usage(self):
        """Typical service unavailable error."""
        error = ServiceUnavailableError(
            "Service temporarily unavailable",
            status_code=503,
        )
        assert error.status_code == 503


class TestExceptionRaising:
    """Tests for raising and catching exceptions."""

    def test_catch_base_exception(self):
        """Can catch all SDK errors with NTLError."""
        with pytest.raises(NTLError):
            raise AuthenticationError("Test")

        with pytest.raises(NTLError):
            raise RateLimitError("Test")

        with pytest.raises(NTLError):
            raise InsufficientCreditsError("Test")

        with pytest.raises(NTLError):
            raise APIError("Test")

    def test_catch_specific_exception(self):
        """Can catch specific exception types."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Auth failed")

        with pytest.raises(RateLimitError):
            raise RateLimitError("Rate limited")

    def test_exception_not_caught_by_wrong_type(self):
        """Exception not caught by unrelated type."""
        with pytest.raises(AuthenticationError):
            try:
                raise AuthenticationError("Auth error")
            except RateLimitError:
                pass  # Should not catch

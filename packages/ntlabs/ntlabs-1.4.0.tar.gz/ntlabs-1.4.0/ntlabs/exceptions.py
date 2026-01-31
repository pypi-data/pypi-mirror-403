"""
NTLabs - Neural Thinkers LAB SDK
SDK Exceptions.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""


class NTLError(Exception):
    """Base exception for NTLabs SDK."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(self.message)


class AuthenticationError(NTLError):
    """Invalid or missing API key."""
    pass


class RateLimitError(NTLError):
    """Rate limit exceeded."""

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class InsufficientCreditsError(NTLError):
    """Not enough credits for the operation."""
    pass


class APIError(NTLError):
    """General API error."""
    pass


class ValidationError(NTLError):
    """Request validation error."""
    pass


class ServiceUnavailableError(NTLError):
    """Service temporarily unavailable."""
    pass

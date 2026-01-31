"""
Email providers.

Available providers:
- ResendProvider: Resend.com API
- SMTPProvider: Standard SMTP
"""

from .base import BaseEmailProvider
from .resend import ResendProvider
from .smtp import SMTPProvider

__all__ = [
    "BaseEmailProvider",
    "ResendProvider",
    "SMTPProvider",
]

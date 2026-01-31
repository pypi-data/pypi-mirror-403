"""
Common validators for general-purpose data validation.

Provides validation functions for:
- Email addresses
- URLs
- UUIDs
- IP addresses
- Passwords (strength checking)
- Dates
"""

import re
import uuid as uuid_module
from datetime import date, datetime
from ipaddress import IPv4Address, IPv6Address, ip_address

# =============================================================================
# Email Validation
# =============================================================================

# RFC 5322 compliant email regex (simplified but robust)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Common disposable email domains
DISPOSABLE_DOMAINS = frozenset(
    {
        "tempmail.com",
        "throwaway.email",
        "guerrillamail.com",
        "mailinator.com",
        "10minutemail.com",
        "temp-mail.org",
        "fakeinbox.com",
        "trashmail.com",
        "maildrop.cc",
        "yopmail.com",
        "sharklasers.com",
        "getairmail.com",
    }
)


def validate_email(email: str, allow_disposable: bool = True) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate
        allow_disposable: If False, rejects known disposable email domains

    Returns:
        True if valid email format, False otherwise

    Example:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid-email")
        False
    """
    if not email or not isinstance(email, str):
        return False

    email = email.strip().lower()

    if not EMAIL_REGEX.match(email):
        return False

    if not allow_disposable:
        domain = email.split("@")[1]
        if domain in DISPOSABLE_DOMAINS:
            return False

    return True


def normalize_email(email: str) -> str:
    """
    Normalize email address (lowercase, trim).

    Args:
        email: Email address to normalize

    Returns:
        Normalized email address
    """
    if not email:
        return ""
    return email.strip().lower()


def get_email_domain(email: str) -> str | None:
    """
    Extract domain from email address.

    Args:
        email: Email address

    Returns:
        Domain part of email or None if invalid

    Example:
        >>> get_email_domain("user@example.com")
        "example.com"
    """
    if not validate_email(email):
        return None
    return email.split("@")[1].lower()


# Alias for backwards compatibility
is_valid_email = validate_email


# =============================================================================
# URL Validation
# =============================================================================

URL_REGEX = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"  # domain...
    r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # ...TLD
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or IP
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def validate_url(
    url: str, require_https: bool = False, allowed_schemes: list | None = None
) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate
        require_https: If True, only accepts HTTPS URLs
        allowed_schemes: List of allowed schemes (e.g., ["http", "https"])

    Returns:
        True if valid URL format, False otherwise

    Example:
        >>> validate_url("https://example.com/path?query=1")
        True
        >>> validate_url("ftp://example.com", allowed_schemes=["http", "https"])
        False
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()

    if require_https and not url.lower().startswith("https://"):
        return False

    if allowed_schemes:
        scheme = url.split("://")[0].lower() if "://" in url else ""
        if scheme not in [s.lower() for s in allowed_schemes]:
            return False

    return bool(URL_REGEX.match(url))


def extract_domain_from_url(url: str) -> str | None:
    """
    Extract domain from URL.

    Args:
        url: URL string

    Returns:
        Domain or None if invalid

    Example:
        >>> extract_domain_from_url("https://www.example.com/path")
        "www.example.com"
    """
    if not url:
        return None

    # Remove scheme
    if "://" in url:
        url = url.split("://")[1]

    # Remove path
    url = url.split("/")[0]

    # Remove port
    url = url.split(":")[0]

    return url.lower() if url else None


# Alias for backwards compatibility
is_valid_url = validate_url


# =============================================================================
# UUID Validation
# =============================================================================


def validate_uuid(value: str, version: int | None = None) -> bool:
    """
    Validate UUID format.

    Args:
        value: String to validate as UUID
        version: If specified, only accepts UUIDs of this version (1, 4, etc.)

    Returns:
        True if valid UUID, False otherwise

    Example:
        >>> validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> validate_uuid("not-a-uuid")
        False
    """
    if not value or not isinstance(value, str):
        return False

    try:
        parsed = uuid_module.UUID(value)
        if version is not None:
            return parsed.version == version
        return True
    except (ValueError, AttributeError):
        return False


def generate_uuid(version: int = 4) -> str:
    """
    Generate a new UUID.

    Args:
        version: UUID version (1 or 4)

    Returns:
        UUID string

    Example:
        >>> generate_uuid()
        "550e8400-e29b-41d4-a716-446655440000"
    """
    if version == 1:
        return str(uuid_module.uuid1())
    return str(uuid_module.uuid4())


# Alias for backwards compatibility
is_valid_uuid = validate_uuid


# =============================================================================
# IP Address Validation
# =============================================================================


def validate_ip(
    ip: str,
    version: int | None = None,
    allow_private: bool = True,
    allow_loopback: bool = True,
) -> bool:
    """
    Validate IP address.

    Args:
        ip: IP address string
        version: If specified, only accepts IPv4 (4) or IPv6 (6)
        allow_private: If False, rejects private IP addresses
        allow_loopback: If False, rejects loopback addresses

    Returns:
        True if valid IP address, False otherwise

    Example:
        >>> validate_ip("192.168.1.1")
        True
        >>> validate_ip("192.168.1.1", allow_private=False)
        False
    """
    if not ip or not isinstance(ip, str):
        return False

    try:
        addr = ip_address(ip)

        if version == 4 and not isinstance(addr, IPv4Address):
            return False
        if version == 6 and not isinstance(addr, IPv6Address):
            return False

        if not allow_private and addr.is_private:
            return False

        if not allow_loopback and addr.is_loopback:
            return False

        return True
    except ValueError:
        return False


def get_ip_version(ip: str) -> int | None:
    """
    Get IP address version.

    Args:
        ip: IP address string

    Returns:
        4 for IPv4, 6 for IPv6, None if invalid
    """
    try:
        addr = ip_address(ip)
        return 4 if isinstance(addr, IPv4Address) else 6
    except ValueError:
        return None


# Alias for backwards compatibility
is_valid_ip = validate_ip


# =============================================================================
# Password Validation
# =============================================================================


def validate_password(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = False,
    special_chars: str = "!@#$%^&*()_+-=[]{}|;:,.<>?",
) -> tuple[bool, list]:
    """
    Validate password strength.

    Args:
        password: Password to validate
        min_length: Minimum required length
        require_uppercase: Require at least one uppercase letter
        require_lowercase: Require at least one lowercase letter
        require_digit: Require at least one digit
        require_special: Require at least one special character
        special_chars: String of allowed special characters

    Returns:
        Tuple of (is_valid, list_of_errors)

    Example:
        >>> validate_password("weakpass")
        (False, ["Password must contain at least one uppercase letter"])
    """
    errors = []

    if not password:
        return False, ["Password cannot be empty"]

    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters")

    if require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if require_digit and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if require_special and not any(c in special_chars for c in password):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors


def calculate_password_strength(password: str) -> int:
    """
    Calculate password strength score (0-100).

    Args:
        password: Password to evaluate

    Returns:
        Strength score from 0 (very weak) to 100 (very strong)
    """
    if not password:
        return 0

    score = 0

    # Length scoring
    length = len(password)
    if length >= 8:
        score += 20
    if length >= 12:
        score += 10
    if length >= 16:
        score += 10

    # Character diversity
    if any(c.isupper() for c in password):
        score += 15
    if any(c.islower() for c in password):
        score += 15
    if any(c.isdigit() for c in password):
        score += 15
    if any(not c.isalnum() for c in password):
        score += 15

    # Deduct for common patterns
    common_patterns = ["123", "abc", "qwerty", "password", "admin"]
    for pattern in common_patterns:
        if pattern in password.lower():
            score -= 10

    return max(0, min(100, score))


# =============================================================================
# Date Validation
# =============================================================================


def validate_date(
    value: str,
    format: str = "%Y-%m-%d",
    min_date: date | None = None,
    max_date: date | None = None,
) -> bool:
    """
    Validate date string.

    Args:
        value: Date string to validate
        format: Expected date format (strptime format)
        min_date: Minimum allowed date
        max_date: Maximum allowed date

    Returns:
        True if valid date, False otherwise

    Example:
        >>> validate_date("2026-01-27")
        True
        >>> validate_date("27/01/2026", format="%d/%m/%Y")
        True
    """
    if not value or not isinstance(value, str):
        return False

    try:
        parsed = datetime.strptime(value, format).date()

        if min_date and parsed < min_date:
            return False

        if max_date and parsed > max_date:
            return False

        return True
    except ValueError:
        return False


def parse_date(value: str, format: str = "%Y-%m-%d") -> date | None:
    """
    Parse date string to date object.

    Args:
        value: Date string to parse
        format: Expected date format

    Returns:
        date object or None if invalid
    """
    try:
        return datetime.strptime(value, format).date()
    except (ValueError, TypeError):
        return None


# Alias for backwards compatibility
is_valid_date = validate_date


# =============================================================================
# Generic Validators
# =============================================================================


def validate_length(
    value: str, min_length: int | None = None, max_length: int | None = None
) -> bool:
    """
    Validate string length.

    Args:
        value: String to validate
        min_length: Minimum length (inclusive)
        max_length: Maximum length (inclusive)

    Returns:
        True if length is within bounds, False otherwise
    """
    if value is None:
        return False

    length = len(value)

    if min_length is not None and length < min_length:
        return False

    if max_length is not None and length > max_length:
        return False

    return True


def validate_numeric_range(
    value: float,
    min_value: float | None = None,
    max_value: float | None = None,
    allow_none: bool = False,
) -> bool:
    """
    Validate numeric value is within range.

    Args:
        value: Number to validate
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        allow_none: If True, None is considered valid

    Returns:
        True if value is within range, False otherwise
    """
    if value is None:
        return allow_none

    if not isinstance(value, (int, float)):
        return False

    if min_value is not None and value < min_value:
        return False

    if max_value is not None and value > max_value:
        return False

    return True

"""
Tests for ntlabs.validators.common module.

Tests common validators including:
- Email addresses
- URLs
- UUIDs
- IP addresses
- Passwords
- Dates
- Generic validators (length, numeric range)
"""

from datetime import date, datetime, timedelta

import pytest

from ntlabs.validators.common import (
    DISPOSABLE_DOMAINS,
    calculate_password_strength,
    extract_domain_from_url,
    generate_uuid,
    get_email_domain,
    get_ip_version,
    is_valid_date,
    is_valid_email,
    is_valid_ip,
    is_valid_url,
    is_valid_uuid,
    normalize_email,
    parse_date,
    validate_date,
    validate_email,
    validate_ip,
    validate_length,
    validate_numeric_range,
    validate_password,
    validate_url,
    validate_uuid,
)


# =============================================================================
# Email Validation Tests
# =============================================================================


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email_simple(self):
        """Test simple valid email."""
        assert validate_email("user@example.com") is True

    def test_valid_email_with_dots(self):
        """Test email with dots in local part."""
        assert validate_email("user.name@example.com") is True
        assert validate_email("first.last@example.com") is True

    def test_valid_email_with_plus(self):
        """Test email with plus sign."""
        assert validate_email("user+tag@example.com") is True
        assert validate_email("user+filter@example.co.uk") is True

    def test_valid_email_with_underscore(self):
        """Test email with underscore."""
        assert validate_email("user_name@example.com") is True

    def test_valid_email_with_percent(self):
        """Test email with percent sign."""
        assert validate_email("user%domain@example.com") is True

    def test_valid_email_subdomain(self):
        """Test email with subdomain."""
        assert validate_email("user@mail.example.com") is True
        assert validate_email("user@deep.sub.domain.com") is True

    def test_valid_email_co_uk(self):
        """Test email with co.uk TLD."""
        assert validate_email("user@example.co.uk") is True

    def test_invalid_email_no_at(self):
        """Test email without @ symbol."""
        assert validate_email("userexample.com") is False

    def test_invalid_email_no_domain(self):
        """Test email without domain."""
        assert validate_email("user@") is False

    def test_invalid_email_no_local(self):
        """Test email without local part."""
        assert validate_email("@example.com") is False

    def test_invalid_email_no_tld(self):
        """Test email without TLD."""
        assert validate_email("user@example") is False

    def test_invalid_email_single_char_tld(self):
        """Test email with single char TLD."""
        assert validate_email("user@example.c") is False

    def test_invalid_email_spaces(self):
        """Test email with spaces."""
        assert validate_email("user name@example.com") is False
        assert validate_email("user@example .com") is False

    def test_invalid_email_empty(self):
        """Test empty email."""
        assert validate_email("") is False

    def test_invalid_email_none(self):
        """Test None email."""
        assert validate_email(None) is False

    def test_invalid_email_integer(self):
        """Test integer input."""
        assert validate_email(12345) is False

    def test_email_whitespace_trimmed(self):
        """Test email with whitespace is trimmed."""
        assert validate_email("  user@example.com  ") is True

    def test_email_disposable_allowed(self):
        """Test disposable email allowed by default."""
        assert validate_email("user@mailinator.com", allow_disposable=True) is True
        assert validate_email("user@tempmail.com", allow_disposable=True) is True

    def test_email_disposable_rejected(self):
        """Test disposable email rejected when not allowed."""
        assert validate_email("user@mailinator.com", allow_disposable=False) is False
        assert validate_email("user@tempmail.com", allow_disposable=False) is False
        assert validate_email("user@yopmail.com", allow_disposable=False) is False

    def test_disposable_domains_constant(self):
        """Test DISPOSABLE_DOMAINS constant."""
        assert "mailinator.com" in DISPOSABLE_DOMAINS
        assert "tempmail.com" in DISPOSABLE_DOMAINS
        assert "yopmail.com" in DISPOSABLE_DOMAINS

    def test_is_valid_email_alias(self):
        """Test is_valid_email is alias for validate_email."""
        assert is_valid_email("user@example.com") is True
        assert is_valid_email("invalid") is False


# =============================================================================
# Email Normalization Tests
# =============================================================================


class TestEmailNormalization:
    """Tests for email normalization."""

    def test_normalize_email_lowercase(self):
        """Test email is lowercased."""
        assert normalize_email("USER@EXAMPLE.COM") == "user@example.com"

    def test_normalize_email_whitespace(self):
        """Test whitespace is trimmed."""
        assert normalize_email("  user@example.com  ") == "user@example.com"

    def test_normalize_email_already_normalized(self):
        """Test already normalized email."""
        assert normalize_email("user@example.com") == "user@example.com"

    def test_normalize_email_empty(self):
        """Test empty email."""
        assert normalize_email("") == ""

    def test_normalize_email_none(self):
        """Test None email."""
        assert normalize_email(None) == ""


# =============================================================================
# Get Email Domain Tests
# =============================================================================


class TestGetEmailDomain:
    """Tests for extracting email domain."""

    def test_get_domain_simple(self):
        """Test simple email domain extraction."""
        assert get_email_domain("user@example.com") == "example.com"

    def test_get_domain_subdomain(self):
        """Test subdomain extraction."""
        assert get_email_domain("user@mail.example.com") == "mail.example.com"

    def test_get_domain_lowercased(self):
        """Test domain is lowercased."""
        assert get_email_domain("user@EXAMPLE.COM") == "example.com"

    def test_get_domain_invalid_email(self):
        """Test invalid email returns None."""
        assert get_email_domain("invalid") is None
        assert get_email_domain("user@") is None

    def test_get_domain_empty(self):
        """Test empty email returns None."""
        assert get_email_domain("") is None


# =============================================================================
# URL Validation Tests
# =============================================================================


class TestURLValidation:
    """Tests for URL validation."""

    def test_valid_url_http(self):
        """Test valid HTTP URL."""
        assert validate_url("http://example.com") is True

    def test_valid_url_https(self):
        """Test valid HTTPS URL."""
        assert validate_url("https://example.com") is True

    def test_valid_url_with_path(self):
        """Test URL with path."""
        assert validate_url("https://example.com/path/to/resource") is True

    def test_valid_url_with_query(self):
        """Test URL with query string."""
        assert validate_url("https://example.com/path?query=value") is True
        assert validate_url("https://example.com/path?a=1&b=2") is True

    def test_valid_url_with_port(self):
        """Test URL with port."""
        assert validate_url("https://example.com:8080") is True
        assert validate_url("http://example.com:3000/path") is True

    def test_valid_url_with_fragment(self):
        """Test URL with fragment."""
        assert validate_url("https://example.com/path#section") is True

    def test_valid_url_localhost(self):
        """Test localhost URL."""
        assert validate_url("http://localhost") is True
        assert validate_url("http://localhost:3000") is True

    def test_valid_url_ip_address(self):
        """Test URL with IP address."""
        assert validate_url("http://192.168.1.1") is True
        assert validate_url("http://127.0.0.1:8080") is True

    def test_valid_url_subdomain(self):
        """Test URL with subdomain."""
        assert validate_url("https://www.example.com") is True
        assert validate_url("https://api.subdomain.example.com") is True

    def test_invalid_url_no_scheme(self):
        """Test URL without scheme."""
        assert validate_url("example.com") is False

    def test_invalid_url_ftp(self):
        """Test FTP URL not accepted."""
        assert validate_url("ftp://example.com") is False

    def test_invalid_url_file(self):
        """Test file URL not accepted."""
        assert validate_url("file:///path/to/file") is False

    def test_invalid_url_empty(self):
        """Test empty URL."""
        assert validate_url("") is False

    def test_invalid_url_none(self):
        """Test None URL."""
        assert validate_url(None) is False

    def test_invalid_url_integer(self):
        """Test integer input."""
        assert validate_url(12345) is False

    def test_url_require_https(self):
        """Test HTTPS requirement."""
        assert validate_url("https://example.com", require_https=True) is True
        assert validate_url("http://example.com", require_https=True) is False

    def test_url_allowed_schemes(self):
        """Test custom allowed schemes - currently only http/https supported in regex."""
        # The URL_REGEX only accepts http/https, so allowed_schemes doesn't change that
        assert validate_url("https://example.com", allowed_schemes=["http", "https"]) is True
        assert validate_url("http://example.com", allowed_schemes=["https"]) is False

    def test_url_whitespace_trimmed(self):
        """Test URL with whitespace is trimmed."""
        assert validate_url("  https://example.com  ") is True

    def test_is_valid_url_alias(self):
        """Test is_valid_url is alias for validate_url."""
        assert is_valid_url("https://example.com") is True
        assert is_valid_url("invalid") is False


# =============================================================================
# Domain Extraction Tests
# =============================================================================


class TestExtractDomainFromURL:
    """Tests for extracting domain from URL."""

    def test_extract_domain_simple(self):
        """Test simple domain extraction."""
        assert extract_domain_from_url("https://example.com") == "example.com"

    def test_extract_domain_with_path(self):
        """Test domain extraction with path."""
        assert extract_domain_from_url("https://example.com/path") == "example.com"

    def test_extract_domain_with_port(self):
        """Test domain extraction with port."""
        assert extract_domain_from_url("https://example.com:8080") == "example.com"

    def test_extract_domain_subdomain(self):
        """Test subdomain extraction."""
        assert extract_domain_from_url("https://www.example.com") == "www.example.com"

    def test_extract_domain_www(self):
        """Test www subdomain extraction."""
        assert extract_domain_from_url("https://www.google.com/path") == "www.google.com"

    def test_extract_domain_lowercase(self):
        """Test domain is lowercased."""
        assert extract_domain_from_url("https://EXAMPLE.COM") == "example.com"

    def test_extract_domain_empty(self):
        """Test empty URL."""
        assert extract_domain_from_url("") is None

    def test_extract_domain_none(self):
        """Test None URL."""
        assert extract_domain_from_url(None) is None

    def test_extract_domain_no_scheme(self):
        """Test URL without scheme."""
        assert extract_domain_from_url("example.com/path") == "example.com"


# =============================================================================
# UUID Validation Tests
# =============================================================================


class TestUUIDValidation:
    """Tests for UUID validation."""

    def test_valid_uuid_v4(self):
        """Test valid UUID v4."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_lowercase(self):
        """Test lowercase UUID."""
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000") is True

    def test_valid_uuid_uppercase(self):
        """Test uppercase UUID."""
        assert validate_uuid("550E8400-E29B-41D4-A716-446655440000") is True

    def test_valid_uuid_v1(self):
        """Test valid UUID v1."""
        # Valid UUID v1 format
        assert validate_uuid("6fa459ea-ee8a-3ca4-894e-db77e160355e") is True

    def test_invalid_uuid_wrong_length(self):
        """Test UUID with wrong length."""
        assert validate_uuid("550e8400-e29b-41d4-a716") is False
        assert validate_uuid("550e8400-e29b-41d4-a716-44665544000") is False

    def test_invalid_uuid_bad_format(self):
        """Test UUID with wrong format."""
        assert validate_uuid("not-a-uuid") is False
        # Note: UUID without hyphens IS valid according to Python's uuid module

    def test_invalid_uuid_empty(self):
        """Test empty UUID."""
        assert validate_uuid("") is False

    def test_invalid_uuid_none(self):
        """Test None UUID."""
        assert validate_uuid(None) is False

    def test_invalid_uuid_integer(self):
        """Test integer input."""
        assert validate_uuid(12345) is False

    def test_uuid_version_match(self):
        """Test UUID with specific version match."""
        # Valid UUID v4
        assert validate_uuid("550e8400-e29b-41d4-a716-446655440000", version=4) is True

    def test_uuid_version_mismatch(self):
        """Test UUID with version mismatch."""
        # UUID v1 tested as v4
        assert validate_uuid("6fa459ea-ee8a-3ca4-894e-db77e160355e", version=4) is False

    def test_uuid_version_1(self):
        """Test UUID version 1 with a valid v1 UUID."""
        # Generate a valid v1 UUID
        uuid_v1 = generate_uuid(version=1)
        assert validate_uuid(uuid_v1, version=1) is True

    def test_is_valid_uuid_alias(self):
        """Test is_valid_uuid is alias for validate_uuid."""
        assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000") is True
        assert is_valid_uuid("invalid") is False


# =============================================================================
# UUID Generation Tests
# =============================================================================


class TestUUIDGeneration:
    """Tests for UUID generation."""

    def test_generate_uuid_v4(self):
        """Test generate UUID v4."""
        uuid = generate_uuid(version=4)
        assert validate_uuid(uuid, version=4) is True

    def test_generate_uuid_default(self):
        """Test generate UUID default (v4)."""
        uuid = generate_uuid()
        assert validate_uuid(uuid, version=4) is True

    def test_generate_uuid_v1(self):
        """Test generate UUID v1."""
        uuid = generate_uuid(version=1)
        assert validate_uuid(uuid, version=1) is True

    def test_generate_unique_uuids(self):
        """Test generated UUIDs are unique."""
        uuid1 = generate_uuid()
        uuid2 = generate_uuid()
        assert uuid1 != uuid2


# =============================================================================
# IP Address Validation Tests
# =============================================================================


class TestIPValidation:
    """Tests for IP address validation."""

    def test_valid_ipv4(self):
        """Test valid IPv4 addresses."""
        assert validate_ip("192.168.1.1") is True
        assert validate_ip("10.0.0.1") is True
        assert validate_ip("255.255.255.255") is True
        assert validate_ip("0.0.0.0") is True
        assert validate_ip("127.0.0.1") is True

    def test_valid_ipv6(self):
        """Test valid IPv6 addresses."""
        assert validate_ip("::1") is True
        assert validate_ip("fe80::1") is True
        assert validate_ip("2001:db8::1") is True
        assert validate_ip("::ffff:192.168.1.1") is True

    def test_invalid_ip_format(self):
        """Test invalid IP formats."""
        assert validate_ip("256.1.1.1") is False  # Out of range
        assert validate_ip("192.168.1") is False  # Missing octet
        assert validate_ip("192.168.1.1.1") is False  # Extra octet
        assert validate_ip("not-an-ip") is False

    def test_invalid_ip_empty(self):
        """Test empty IP."""
        assert validate_ip("") is False

    def test_invalid_ip_none(self):
        """Test None IP."""
        assert validate_ip(None) is False

    def test_ip_version_4(self):
        """Test IPv4 version check."""
        assert validate_ip("192.168.1.1", version=4) is True
        assert validate_ip("::1", version=4) is False

    def test_ip_version_6(self):
        """Test IPv6 version check."""
        assert validate_ip("::1", version=6) is True
        assert validate_ip("192.168.1.1", version=6) is False

    def test_ip_private_allowed(self):
        """Test private IP allowed by default."""
        assert validate_ip("192.168.1.1", allow_private=True) is True
        assert validate_ip("10.0.0.1", allow_private=True) is True

    def test_ip_private_rejected(self):
        """Test private IP rejected when not allowed."""
        assert validate_ip("192.168.1.1", allow_private=False) is False
        assert validate_ip("10.0.0.1", allow_private=False) is False

    def test_ip_loopback_allowed(self):
        """Test loopback allowed by default."""
        assert validate_ip("127.0.0.1", allow_loopback=True) is True
        assert validate_ip("::1", allow_loopback=True) is True

    def test_ip_loopback_rejected(self):
        """Test loopback rejected when not allowed."""
        assert validate_ip("127.0.0.1", allow_loopback=False) is False
        assert validate_ip("::1", allow_loopback=False) is False

    def test_is_valid_ip_alias(self):
        """Test is_valid_ip is alias for validate_ip."""
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("invalid") is False


# =============================================================================
# IP Version Tests
# =============================================================================


class TestGetIPVersion:
    """Tests for getting IP version."""

    def test_get_version_ipv4(self):
        """Test getting version for IPv4."""
        assert get_ip_version("192.168.1.1") == 4
        assert get_ip_version("127.0.0.1") == 4

    def test_get_version_ipv6(self):
        """Test getting version for IPv6."""
        assert get_ip_version("::1") == 6
        assert get_ip_version("fe80::1") == 6

    def test_get_version_invalid(self):
        """Test getting version for invalid IP."""
        assert get_ip_version("invalid") is None
        assert get_ip_version("") is None


# =============================================================================
# Password Validation Tests
# =============================================================================


class TestPasswordValidation:
    """Tests for password validation."""

    def test_valid_password_strong(self):
        """Test strong password."""
        is_valid, errors = validate_password("SecurePass123!")
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_password_minimum(self):
        """Test password meeting minimum requirements."""
        is_valid, errors = validate_password("Password1")
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_password_too_short(self):
        """Test password too short."""
        is_valid, errors = validate_password("Short1")
        assert is_valid is False
        assert any("8 characters" in e for e in errors)

    def test_invalid_password_no_uppercase(self):
        """Test password without uppercase."""
        is_valid, errors = validate_password("password123")
        assert is_valid is False
        assert any("uppercase" in e for e in errors)

    def test_invalid_password_no_lowercase(self):
        """Test password without lowercase."""
        is_valid, errors = validate_password("PASSWORD123")
        assert is_valid is False
        assert any("lowercase" in e for e in errors)

    def test_invalid_password_no_digit(self):
        """Test password without digit."""
        is_valid, errors = validate_password("PasswordABC")
        assert is_valid is False
        assert any("digit" in e for e in errors)

    def test_invalid_password_no_special(self):
        """Test password without special char when required."""
        is_valid, errors = validate_password("Password123", require_special=True)
        assert is_valid is False
        assert any("special character" in e for e in errors)

    def test_valid_password_with_special(self):
        """Test password with special char."""
        is_valid, errors = validate_password("Password123!", require_special=True)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_password_empty(self):
        """Test empty password."""
        is_valid, errors = validate_password("")
        assert is_valid is False
        assert any("empty" in e.lower() for e in errors)

    def test_custom_min_length(self):
        """Test custom minimum length."""
        is_valid, errors = validate_password("Pass1", min_length=4)
        assert is_valid is True

    def test_custom_special_chars(self):
        """Test custom special characters."""
        is_valid, errors = validate_password("Password123@", require_special=True, special_chars="@#$")
        assert is_valid is True

    def test_custom_special_chars_wrong(self):
        """Test wrong special character."""
        is_valid, errors = validate_password("Password123!", require_special=True, special_chars="@#$")
        assert is_valid is False

    def test_no_requirements(self):
        """Test password with no special requirements."""
        is_valid, errors = validate_password(
            "password",
            require_uppercase=False,
            require_lowercase=False,
            require_digit=False,
            require_special=False,
        )
        assert is_valid is True


# =============================================================================
# Password Strength Tests
# =============================================================================


class TestPasswordStrength:
    """Tests for password strength calculation."""

    def test_strength_empty(self):
        """Test empty password strength."""
        assert calculate_password_strength("") == 0

    def test_strength_very_weak(self):
        """Test very weak password."""
        strength = calculate_password_strength("a")
        assert strength < 30

    def test_strength_weak(self):
        """Test weak password."""
        strength = calculate_password_strength("password")
        assert strength < 50

    def test_strength_medium(self):
        """Test medium password."""
        strength = calculate_password_strength("Password1")
        assert 40 <= strength <= 70

    def test_strength_strong(self):
        """Test strong password."""
        strength = calculate_password_strength("SecurePassword123!")
        assert strength > 60

    def test_strength_very_strong(self):
        """Test very strong password."""
        strength = calculate_password_strength("My$uper$trongP@ssw0rd!!")
        assert strength > 80

    def test_strength_length_bonus(self):
        """Test length bonus."""
        short = calculate_password_strength("Pass1!")
        medium = calculate_password_strength("Password1!")
        long = calculate_password_strength("VeryLongPassword123!")
        very_long = calculate_password_strength("ExtremelyLongPassword123!!!")

        assert medium > short
        assert long > medium
        assert very_long >= long

    def test_strength_pattern_deduction(self):
        """Test pattern deduction."""
        with_pattern = calculate_password_strength("password123")
        without_pattern = calculate_password_strength("xK9$mP2@vL")
        assert without_pattern > with_pattern

    def test_strength_max_100(self):
        """Test strength capped at 100."""
        strength = calculate_password_strength("A" * 50 + "1!" * 10)
        assert strength <= 100

    def test_strength_min_0(self):
        """Test strength minimum of 0."""
        strength = calculate_password_strength("123qwerty")
        assert strength >= 0


# =============================================================================
# Date Validation Tests
# =============================================================================


class TestDateValidation:
    """Tests for date validation."""

    def test_valid_date_default_format(self):
        """Test valid date in default format (YYYY-MM-DD)."""
        assert validate_date("2024-01-15") is True
        assert validate_date("2024-12-31") is True

    def test_valid_date_custom_format(self):
        """Test valid date in custom format."""
        assert validate_date("15/01/2024", format="%d/%m/%Y") is True
        assert validate_date("31-12-2024", format="%d-%m-%Y") is True
        assert validate_date("Jan 15, 2024", format="%b %d, %Y") is True

    def test_invalid_date_format(self):
        """Test invalid date format."""
        assert validate_date("15/01/2024") is False  # Wrong format
        assert validate_date("2024/01/15") is False  # Wrong format

    def test_invalid_date_values(self):
        """Test invalid date values."""
        assert validate_date("2024-13-01") is False  # Invalid month
        assert validate_date("2024-01-32") is False  # Invalid day
        assert validate_date("2024-02-30") is False  # Feb 30 doesn't exist

    def test_invalid_date_empty(self):
        """Test empty date."""
        assert validate_date("") is False

    def test_invalid_date_none(self):
        """Test None date."""
        assert validate_date(None) is False

    def test_valid_date_with_min_date(self):
        """Test date with minimum date constraint."""
        min_date = date(2024, 1, 1)
        assert validate_date("2024-01-15", min_date=min_date) is True
        assert validate_date("2023-12-31", min_date=min_date) is False

    def test_valid_date_with_max_date(self):
        """Test date with maximum date constraint."""
        max_date = date(2024, 12, 31)
        assert validate_date("2024-06-15", max_date=max_date) is True
        assert validate_date("2025-01-01", max_date=max_date) is False

    def test_valid_date_with_min_max(self):
        """Test date with both min and max constraints."""
        min_date = date(2024, 1, 1)
        max_date = date(2024, 12, 31)
        assert validate_date("2024-06-15", min_date=min_date, max_date=max_date) is True
        assert validate_date("2023-12-31", min_date=min_date, max_date=max_date) is False
        assert validate_date("2025-01-01", min_date=min_date, max_date=max_date) is False

    def test_is_valid_date_alias(self):
        """Test is_valid_date is alias for validate_date."""
        assert is_valid_date("2024-01-15") is True
        assert is_valid_date("invalid") is False


# =============================================================================
# Date Parsing Tests
# =============================================================================


class TestDateParsing:
    """Tests for date parsing."""

    def test_parse_date_default_format(self):
        """Test parse date in default format."""
        result = parse_date("2024-01-15")
        assert result == date(2024, 1, 15)

    def test_parse_date_custom_format(self):
        """Test parse date in custom format."""
        result = parse_date("15/01/2024", format="%d/%m/%Y")
        assert result == date(2024, 1, 15)

    def test_parse_date_invalid(self):
        """Test parse invalid date."""
        assert parse_date("invalid") is None
        assert parse_date("2024-13-01") is None

    def test_parse_date_empty(self):
        """Test parse empty date."""
        assert parse_date("") is None

    def test_parse_date_none(self):
        """Test parse None date."""
        assert parse_date(None) is None


# =============================================================================
# Length Validation Tests
# =============================================================================


class TestLengthValidation:
    """Tests for string length validation."""

    def test_length_no_constraints(self):
        """Test length with no constraints."""
        assert validate_length("hello") is True
        assert validate_length("") is True

    def test_length_min_only(self):
        """Test length with minimum only."""
        assert validate_length("hello", min_length=3) is True
        assert validate_length("hi", min_length=3) is False
        assert validate_length("", min_length=1) is False

    def test_length_max_only(self):
        """Test length with maximum only."""
        assert validate_length("hello", max_length=10) is True
        assert validate_length("hello world", max_length=10) is False

    def test_length_min_and_max(self):
        """Test length with both min and max."""
        assert validate_length("hello", min_length=3, max_length=10) is True
        assert validate_length("hi", min_length=3, max_length=10) is False
        assert validate_length("hello world", min_length=3, max_length=10) is False

    def test_length_exact(self):
        """Test length exact match."""
        assert validate_length("hello", min_length=5, max_length=5) is True
        assert validate_length("hi", min_length=5, max_length=5) is False

    def test_length_empty_string(self):
        """Test length with empty string."""
        assert validate_length("", min_length=0) is True
        assert validate_length("", max_length=0) is True

    def test_length_none(self):
        """Test length with None."""
        assert validate_length(None) is False
        assert validate_length(None, min_length=0) is False


# =============================================================================
# Numeric Range Validation Tests
# =============================================================================


class TestNumericRangeValidation:
    """Tests for numeric range validation."""

    def test_range_no_constraints(self):
        """Test range with no constraints."""
        assert validate_numeric_range(100) is True
        assert validate_numeric_range(-100) is True

    def test_range_min_only(self):
        """Test range with minimum only."""
        assert validate_numeric_range(100, min_value=50) is True
        assert validate_numeric_range(100, min_value=100) is True
        assert validate_numeric_range(100, min_value=101) is False

    def test_range_max_only(self):
        """Test range with maximum only."""
        assert validate_numeric_range(100, max_value=150) is True
        assert validate_numeric_range(100, max_value=100) is True
        assert validate_numeric_range(100, max_value=99) is False

    def test_range_min_and_max(self):
        """Test range with both min and max."""
        assert validate_numeric_range(100, min_value=50, max_value=150) is True
        assert validate_numeric_range(100, min_value=100, max_value=100) is True
        assert validate_numeric_range(100, min_value=101, max_value=150) is False
        assert validate_numeric_range(100, min_value=50, max_value=99) is False

    def test_range_with_none(self):
        """Test range with None value."""
        assert validate_numeric_range(None) is False
        assert validate_numeric_range(None, allow_none=True) is True
        assert validate_numeric_range(None, allow_none=False) is False

    def test_range_non_numeric(self):
        """Test range with non-numeric value."""
        assert validate_numeric_range("100") is False
        assert validate_numeric_range("hello") is False

    def test_range_with_float(self):
        """Test range with float values."""
        assert validate_numeric_range(100.5, min_value=100, max_value=101) is True
        assert validate_numeric_range(100.0, min_value=100, max_value=100) is True

    def test_range_with_negative(self):
        """Test range with negative values."""
        assert validate_numeric_range(-50, min_value=-100, max_value=0) is True
        assert validate_numeric_range(-150, min_value=-100, max_value=0) is False

    def test_range_zero(self):
        """Test range with zero."""
        assert validate_numeric_range(0, min_value=0) is True
        assert validate_numeric_range(0, max_value=0) is True
        assert validate_numeric_range(0, min_value=1) is False

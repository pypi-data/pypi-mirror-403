"""
NTLabs SDK - Client Tests
Tests for the main NTLClient class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

from unittest.mock import MagicMock, patch

import pytest

from ntlabs import NTLClient
from ntlabs.exceptions import (
    APIError,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    ServiceUnavailableError,
)


class TestClientInitialization:
    """Tests for client initialization."""

    def test_init_with_api_key(self):
        """Client initializes with explicit API key."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert client.api_key == "ntl_test_123"

    def test_init_with_env_var(self, monkeypatch):
        """Client reads API key from environment."""
        monkeypatch.setenv("NTL_API_KEY", "ntl_env_456")
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient()
            assert client.api_key == "ntl_env_456"

    def test_init_without_api_key_raises(self):
        """Client raises error when no API key provided."""
        with pytest.raises(AuthenticationError) as exc_info:
            NTLClient()
        assert "API key required" in str(exc_info.value)

    def test_init_with_custom_base_url(self):
        """Client accepts custom base URL."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(
                api_key="ntl_test_123", base_url="https://custom.api.com"
            )
            assert client.base_url == "https://custom.api.com"

    def test_init_with_timeout(self):
        """Client accepts custom timeout."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123", timeout=30.0)
            assert client.timeout == 30.0

    def test_init_with_source_system(self):
        """Client accepts explicit source system."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123", source_system="custom_app")
            assert client.source_system == "custom_app"


class TestSourceSystemDetection:
    """Tests for automatic source system detection."""

    def test_detect_hipocrates(self):
        """Detects Hipocrates from API key prefix."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_hipo_abc123")
            assert client.source_system == "hipocrates"

    def test_detect_mercurius(self):
        """Detects Mercurius from API key prefix."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_merc_xyz789")
            assert client.source_system == "mercurius"

    def test_detect_external(self):
        """Defaults to external for unknown prefixes."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_other_123")
            assert client.source_system == "external"


class TestResourceInitialization:
    """Tests for resource initialization."""

    def test_chat_resource_initialized(self):
        """Chat resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "chat")
            assert client.chat is not None

    def test_email_resource_initialized(self):
        """Email resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "email")
            assert client.email is not None

    def test_gov_resource_initialized(self):
        """Gov resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "gov")
            assert client.gov is not None

    def test_transcribe_resource_initialized(self):
        """Transcribe resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "transcribe")
            assert client.transcribe is not None

    def test_billing_resource_initialized(self):
        """Billing resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "billing")
            assert client.billing is not None

    def test_saude_resource_initialized(self):
        """Saude resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "saude")
            assert client.saude is not None

    def test_cartorio_resource_initialized(self):
        """Cartorio resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "cartorio")
            assert client.cartorio is not None

    def test_ibge_resource_initialized(self):
        """IBGE resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "ibge")
            assert client.ibge is not None

    def test_rnds_resource_initialized(self):
        """RNDS resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "rnds")
            assert client.rnds is not None

    def test_bb_resource_initialized(self):
        """BB resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "bb")
            assert client.bb is not None

    def test_auth_resource_initialized(self):
        """Auth resource is initialized."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert hasattr(client, "auth")
            assert client.auth is not None


class TestRequestHandling:
    """Tests for HTTP request handling."""

    def test_successful_get_request(self, mock_client, mock_response):
        """GET request returns parsed JSON."""
        mock_client._mock_http.request.return_value = mock_response(
            {"data": "test_value"}
        )

        result = mock_client.get("/test-endpoint")

        assert result == {"data": "test_value"}
        mock_client._mock_http.request.assert_called_once()

    def test_successful_post_request(self, mock_client, mock_response):
        """POST request sends JSON body."""
        mock_client._mock_http.request.return_value = mock_response({"id": "123"})

        result = mock_client.post("/test-endpoint", json={"key": "value"})

        assert result == {"id": "123"}

    def test_401_raises_authentication_error(self, mock_client, mock_response):
        """401 response raises AuthenticationError."""
        mock_client._mock_http.request.return_value = mock_response(
            {"detail": "Invalid API key"}, status_code=401
        )

        with pytest.raises(AuthenticationError) as exc_info:
            mock_client.get("/test")

        assert "Invalid API key" in str(exc_info.value)
        assert exc_info.value.status_code == 401

    def test_402_raises_insufficient_credits_error(self, mock_client, mock_response):
        """402 response raises InsufficientCreditsError."""
        mock_client._mock_http.request.return_value = mock_response(
            {"detail": "Not enough credits"}, status_code=402
        )

        with pytest.raises(InsufficientCreditsError) as exc_info:
            mock_client.get("/test")

        assert exc_info.value.status_code == 402

    def test_429_raises_rate_limit_error(self, mock_client, mock_response):
        """429 response raises RateLimitError with retry_after."""
        response = mock_response({"detail": "Too many requests"}, status_code=429)
        response.headers = {"Retry-After": "30"}
        mock_client._mock_http.request.return_value = response

        with pytest.raises(RateLimitError) as exc_info:
            mock_client.get("/test")

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 30

    def test_503_raises_service_unavailable_error(self, mock_client, mock_response):
        """503 response raises ServiceUnavailableError."""
        mock_client._mock_http.request.return_value = mock_response({}, status_code=503)

        with pytest.raises(ServiceUnavailableError) as exc_info:
            mock_client.get("/test")

        assert exc_info.value.status_code == 503

    def test_500_raises_api_error(self, mock_client, mock_response):
        """500 response raises APIError."""
        mock_client._mock_http.request.return_value = mock_response(
            {"detail": "Internal server error"}, status_code=500
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/test")

        assert exc_info.value.status_code == 500

    def test_timeout_raises_api_error(self, mock_client):
        """Timeout raises APIError."""
        import httpx

        mock_client._mock_http.request.side_effect = httpx.TimeoutException(
            "Connection timeout"
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/test")

        assert "timeout" in str(exc_info.value).lower()

    def test_request_error_raises_api_error(self, mock_client):
        """Request error raises APIError."""
        import httpx

        mock_client._mock_http.request.side_effect = httpx.RequestError(
            "Connection refused"
        )

        with pytest.raises(APIError) as exc_info:
            mock_client.get("/test")

        assert "Request failed" in str(exc_info.value)


class TestContextManager:
    """Tests for context manager support."""

    def test_context_manager_closes_client(self):
        """Client closes when exiting context."""
        with patch("ntlabs.client.httpx.Client") as mock_httpx:
            mock_http = MagicMock()
            mock_httpx.return_value = mock_http

            with NTLClient(api_key="ntl_test_123"):
                pass

            mock_http.close.assert_called_once()

    def test_explicit_close(self):
        """Client can be closed explicitly."""
        with patch("ntlabs.client.httpx.Client") as mock_httpx:
            mock_http = MagicMock()
            mock_httpx.return_value = mock_http

            client = NTLClient(api_key="ntl_test_123")
            client.close()

            mock_http.close.assert_called_once()


class TestBaseUrlResolution:
    """Tests for base URL resolution."""

    def test_default_base_url(self):
        """Uses default production URL."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert "neural-lab" in client.base_url

    def test_internal_url_priority(self, monkeypatch):
        """NTL_INTERNAL_URL takes priority."""
        monkeypatch.setenv("NTL_INTERNAL_URL", "http://internal.railway")
        monkeypatch.setenv("NTL_API_URL", "https://public.api")

        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert client.base_url == "http://internal.railway"

    def test_api_url_fallback(self, monkeypatch):
        """NTL_API_URL used when internal not set."""
        monkeypatch.setenv("NTL_API_URL", "https://custom.api.com")

        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123")
            assert client.base_url == "https://custom.api.com"

    def test_explicit_url_overrides_env(self, monkeypatch):
        """Explicit base_url overrides environment."""
        monkeypatch.setenv("NTL_API_URL", "https://env.api.com")

        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(
                api_key="ntl_test_123", base_url="https://explicit.api.com"
            )
            assert client.base_url == "https://explicit.api.com"

    def test_trailing_slash_removed(self):
        """Trailing slash is removed from base URL."""
        with patch("ntlabs.client.httpx.Client"):
            client = NTLClient(api_key="ntl_test_123", base_url="https://api.com/")
            assert client.base_url == "https://api.com"

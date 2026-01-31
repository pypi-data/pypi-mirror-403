"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Extended tests for async client module
Version: 1.0.0
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ntlabs.async_client import AsyncNTLClient, _get_base_url, DEFAULT_BASE_URL
from ntlabs.exceptions import (
    APIError,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    ServiceUnavailableError,
)


class TestGetBaseUrl:
    """Test _get_base_url function."""

    def test_default_url(self):
        """Test default URL when no env vars set."""
        with patch.dict(os.environ, {}, clear=True):
            url = _get_base_url()
            assert url == DEFAULT_BASE_URL

    def test_internal_url_priority(self):
        """Test that internal URL has priority."""
        env_vars = {
            "NTL_INTERNAL_URL": "http://internal:8080",
            "NTL_API_URL": "https://api.example.com",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            url = _get_base_url()
            assert url == "http://internal:8080"

    def test_api_url_fallback(self):
        """Test API URL fallback."""
        env_vars = {
            "NTL_API_URL": "https://api.example.com",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            url = _get_base_url()
            assert url == "https://api.example.com"


class TestAsyncNTLClientInit:
    """Test AsyncNTLClient initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = AsyncNTLClient(api_key="ntl_hipo_test123")
        assert client.api_key == "ntl_hipo_test123"
        assert client.source_system == "hipocrates"

    def test_init_from_env(self):
        """Test initialization from environment variable."""
        with patch.dict(os.environ, {"NTL_API_KEY": "ntl_merc_test456"}):
            client = AsyncNTLClient()
            assert client.api_key == "ntl_merc_test456"
            assert client.source_system == "mercurius"

    def test_init_no_api_key_raises(self):
        """Test that initialization fails without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(AuthenticationError):
                AsyncNTLClient()

    def test_init_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = AsyncNTLClient(
            api_key="ntl_test_key",
            base_url="https://custom.example.com",
        )
        assert client.base_url == "https://custom.example.com"

    def test_init_trailing_slash_removed(self):
        """Test that trailing slash is removed from base URL."""
        client = AsyncNTLClient(
            api_key="ntl_test_key",
            base_url="https://api.example.com/",
        )
        assert client.base_url == "https://api.example.com"

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        client = AsyncNTLClient(
            api_key="ntl_test_key",
            timeout=120.0,
        )
        assert client.timeout == 120.0

    def test_init_custom_source_system(self):
        """Test initialization with custom source system."""
        client = AsyncNTLClient(
            api_key="ntl_test_key",
            source_system="custom_system",
        )
        assert client.source_system == "custom_system"

    def test_detect_hipocrates_system(self):
        """Test auto-detection of Hipocrates system."""
        client = AsyncNTLClient(api_key="ntl_hipo_abc123")
        assert client.source_system == "hipocrates"

    def test_detect_mercurius_system(self):
        """Test auto-detection of Mercurius system."""
        client = AsyncNTLClient(api_key="ntl_merc_abc123")
        assert client.source_system == "mercurius"

    def test_detect_polis_system(self):
        """Test auto-detection of Polis system."""
        client = AsyncNTLClient(api_key="ntl_poli_abc123")
        assert client.source_system == "polis"

    def test_detect_external_system(self):
        """Test auto-detection of external system."""
        client = AsyncNTLClient(api_key="ntl_other_abc123")
        assert client.source_system == "external"

    def test_lazy_client_initialization(self):
        """Test that HTTP client is lazily initialized."""
        client = AsyncNTLClient(api_key="ntl_test_key")
        assert client._client is None

    def test_get_client_creates_instance(self):
        """Test that _get_client creates HTTP client."""
        client = AsyncNTLClient(api_key="ntl_test_key")
        http_client = client._get_client()

        assert isinstance(http_client, httpx.AsyncClient)
        assert client._client is http_client

    def test_get_client_returns_existing(self):
        """Test that _get_client returns existing client."""
        client = AsyncNTLClient(api_key="ntl_test_key")
        client1 = client._get_client()
        client2 = client._get_client()

        assert client1 is client2

    def test_client_headers(self):
        """Test that client has correct headers."""
        client = AsyncNTLClient(
            api_key="ntl_test_key",
            source_system="test",
        )
        http_client = client._get_client()

        headers = http_client.headers
        assert headers["X-API-Key"] == "ntl_test_key"
        assert headers["X-Source-System"] == "test"
        assert "ntlabs-python" in headers["User-Agent"]


class TestAsyncNTLClientResources:
    """Test lazy resource loading."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return AsyncNTLClient(api_key="ntl_test_key")

    def test_auth_resource_lazy_load(self, client):
        """Test auth resource lazy loading."""
        assert client._auth is None
        auth = client.auth
        assert auth is not None
        assert client._auth is auth

    def test_chat_resource_lazy_load(self, client):
        """Test chat resource lazy loading."""
        assert client._chat is None
        chat = client.chat
        assert chat is not None
        assert client._chat is chat

    def test_email_resource_lazy_load(self, client):
        """Test email resource lazy loading."""
        assert client._email is None
        email = client.email
        assert email is not None
        assert client._email is email

    def test_transcribe_resource_lazy_load(self, client):
        """Test transcribe resource lazy loading."""
        assert client._transcribe is None
        transcribe = client.transcribe
        assert transcribe is not None
        assert client._transcribe is transcribe

    def test_gov_resource_lazy_load(self, client):
        """Test gov resource lazy loading."""
        assert client._gov is None
        gov = client.gov
        assert gov is not None
        assert client._gov is gov

    def test_bb_resource_lazy_load(self, client):
        """Test BB resource lazy loading."""
        assert client._bb is None
        bb = client.bb
        assert bb is not None
        assert client._bb is bb

    def test_ibge_resource_lazy_load(self, client):
        """Test IBGE resource lazy loading."""
        assert client._ibge is None
        ibge = client.ibge
        assert ibge is not None
        assert client._ibge is ibge

    def test_saude_resource_lazy_load(self, client):
        """Test saude resource lazy loading."""
        assert client._saude is None
        saude = client.saude
        assert saude is not None
        assert client._saude is saude

    def test_cartorio_resource_lazy_load(self, client):
        """Test cartorio resource lazy loading."""
        assert client._cartorio is None
        cartorio = client.cartorio
        assert cartorio is not None
        assert client._cartorio is cartorio

    def test_rnds_resource_lazy_load(self, client):
        """Test RNDS resource lazy loading."""
        assert client._rnds is None
        rnds = client.rnds
        assert rnds is not None
        assert client._rnds is rnds

    def test_crc_resource_lazy_load(self, client):
        """Test CRC resource lazy loading."""
        assert client._crc is None
        crc = client.crc
        assert crc is not None
        assert client._crc is crc

    def test_censec_resource_lazy_load(self, client):
        """Test CENSEC resource lazy loading."""
        assert client._censec is None
        censec = client.censec
        assert censec is not None
        assert client._censec is censec

    def test_enotariado_resource_lazy_load(self, client):
        """Test e-Notariado resource lazy loading."""
        assert client._enotariado is None
        enotariado = client.enotariado
        assert enotariado is not None
        assert client._enotariado is enotariado

    def test_onr_resource_lazy_load(self, client):
        """Test ONR resource lazy loading."""
        assert client._onr is None
        onr = client.onr
        assert onr is not None
        assert client._onr is onr

    def test_billing_resource_lazy_load(self, client):
        """Test billing resource lazy loading."""
        assert client._billing is None
        billing = client.billing
        assert billing is not None
        assert client._billing is billing


class TestAsyncNTLClientRequest:
    """Test HTTP request methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return AsyncNTLClient(api_key="ntl_test_key")

    @pytest.mark.asyncio
    async def test_successful_request(self, client):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            result = await client.request("GET", "/test")
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_request_with_body(self, client):
        """Test request with JSON body."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"id": 1}'
        mock_response.json.return_value = {"id": 1}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            await client.request("POST", "/test", json={"name": "test"})

            call_args = mock_client.request.call_args
            assert call_args[1]["json"] == {"name": "test"}

    @pytest.mark.asyncio
    async def test_request_with_params(self, client):
        """Test request with query parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{}'
        mock_response.json.return_value = {}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            await client.request("GET", "/test", params={"page": 1})

            call_args = mock_client.request.call_args
            assert call_args[1]["params"] == {"page": 1}

    @pytest.mark.asyncio
    async def test_request_with_headers(self, client):
        """Test request with custom headers."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{}'
        mock_response.json.return_value = {}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            await client.request("GET", "/test", headers={"X-Custom": "value"})

            call_args = mock_client.request.call_args
            assert call_args[1]["headers"]["X-Custom"] == "value"

    @pytest.mark.asyncio
    async def test_authentication_error(self, client):
        """Test handling of 401 response."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.content = b'{"detail": "Invalid API key"}'
        mock_response.json.return_value = {"detail": "Invalid API key"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            with pytest.raises(AuthenticationError) as exc_info:
                await client.request("GET", "/test")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_insufficient_credits_error(self, client):
        """Test handling of 402 response."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.content = b'{"detail": "No credits"}'
        mock_response.json.return_value = {"detail": "No credits"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            with pytest.raises(InsufficientCreditsError) as exc_info:
                await client.request("GET", "/test")

            assert exc_info.value.status_code == 402

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, client):
        """Test handling of 429 response."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.content = b'{"detail": "Rate limited"}'
        mock_response.json.return_value = {"detail": "Rate limited"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            with pytest.raises(RateLimitError) as exc_info:
                await client.request("GET", "/test")

            assert exc_info.value.status_code == 429
            assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    async def test_service_unavailable_error(self, client):
        """Test handling of 503 response."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.content = b""

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            with pytest.raises(ServiceUnavailableError) as exc_info:
                await client.request("GET", "/test")

            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_generic_api_error(self, client):
        """Test handling of generic 4xx/5xx response."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b'{"detail": "Server error"}'
        mock_response.json.return_value = {"detail": "Server error"}

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            with pytest.raises(APIError) as exc_info:
                await client.request("GET", "/test")

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_timeout_exception(self, client):
        """Test handling of timeout exception."""
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.TimeoutException("Request timeout")

        with patch.object(client, "_get_client", return_value=mock_client):
            with pytest.raises(APIError) as exc_info:
                await client.request("GET", "/test")

            assert "timeout" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_request_error(self, client):
        """Test handling of request error."""
        mock_client = AsyncMock()
        mock_client.request.side_effect = httpx.RequestError("Connection failed")

        with patch.object(client, "_get_client", return_value=mock_client):
            with pytest.raises(APIError) as exc_info:
                await client.request("GET", "/test")

            assert "failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_empty_response(self, client):
        """Test handling of empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.content = b""

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response

        with patch.object(client, "_get_client", return_value=mock_client):
            result = await client.request("DELETE", "/test")
            assert result == {}


class TestAsyncNTLClientConvenienceMethods:
    """Test convenience HTTP methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return AsyncNTLClient(api_key="ntl_test_key")

    @pytest.mark.asyncio
    async def test_get_method(self, client):
        """Test GET convenience method."""
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {"data": []}
            result = await client.get("/test", params={"page": 1})

            mock_request.assert_called_once_with("GET", "/test", params={"page": 1})
            assert result == {"data": []}

    @pytest.mark.asyncio
    async def test_post_method(self, client):
        """Test POST convenience method."""
        with patch.object(client, "request") as mock_request:
            mock_request.return_value = {"id": 1}
            result = await client.post("/test", json={"name": "test"})

            mock_request.assert_called_once_with("POST", "/test", json={"name": "test"})
            assert result == {"id": 1}


class TestAsyncNTLClientContextManager:
    """Test async context manager."""

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager usage."""
        client = AsyncNTLClient(api_key="ntl_test_key")

        with patch.object(client, "close") as mock_close:
            async with client:
                pass

            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test closing HTTP client."""
        client = AsyncNTLClient(api_key="ntl_test_key")
        mock_http_client = AsyncMock()
        client._client = mock_http_client

        await client.close()

        mock_http_client.aclose.assert_called_once()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self):
        """Test closing when no client exists."""
        client = AsyncNTLClient(api_key="ntl_test_key")
        client._client = None

        # Should not raise
        await client.close()

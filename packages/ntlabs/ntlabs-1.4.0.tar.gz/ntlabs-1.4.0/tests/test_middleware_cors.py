"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for CORS middleware
Version: 1.0.0
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from ntlabs.middleware.cors import (
    setup_cors,
    get_cors_origins_from_env,
    CORSPresets,
)


class TestSetupCORS:
    """Test CORS setup function."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        app = MagicMock()
        app.add_middleware = MagicMock()
        return app

    def test_setup_cors_development_mode(self, mock_app):
        """Test CORS setup in development mode."""
        with patch("fastapi.middleware.cors.CORSMiddleware") as mock_cors:
            setup_cors(mock_app, development_mode=True)

            mock_app.add_middleware.assert_called_once()
            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_origins"] == ["*"]

    def test_setup_cors_single_origin(self, mock_app):
        """Test CORS setup with single origin."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            setup_cors(
                mock_app,
                origins="https://example.com",
            )

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_origins"] == ["https://example.com"]

    def test_setup_cors_multiple_origins(self, mock_app):
        """Test CORS setup with multiple origins."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            origins = [
                "https://app.example.com",
                "https://admin.example.com",
            ]
            setup_cors(mock_app, origins=origins)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_origins"] == origins

    def test_setup_cors_no_origins(self, mock_app):
        """Test CORS setup with no origins specified."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            setup_cors(mock_app)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_origins"] == []

    def test_setup_cors_custom_methods(self, mock_app):
        """Test CORS setup with custom allowed methods."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            methods = ["GET", "POST"]
            setup_cors(mock_app, origins=["*"], allow_methods=methods)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_methods"] == methods

    def test_setup_cors_default_methods(self, mock_app):
        """Test CORS setup with default methods."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            setup_cors(mock_app, origins=["*"])

            call_args = mock_app.add_middleware.call_args
            assert "GET" in call_args[1]["allow_methods"]
            assert "POST" in call_args[1]["allow_methods"]
            assert "DELETE" in call_args[1]["allow_methods"]

    def test_setup_cors_custom_headers(self, mock_app):
        """Test CORS setup with custom headers."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            headers = ["X-Custom-Header"]
            setup_cors(mock_app, origins=["*"], allow_headers=headers)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_headers"] == headers

    def test_setup_cors_default_headers(self, mock_app):
        """Test CORS setup with default headers."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            setup_cors(mock_app, origins=["*"])

            call_args = mock_app.add_middleware.call_args
            assert "Authorization" in call_args[1]["allow_headers"]
            assert "Content-Type" in call_args[1]["allow_headers"]

    def test_setup_cors_expose_headers(self, mock_app):
        """Test CORS setup with exposed headers."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            setup_cors(mock_app, origins=["*"])

            call_args = mock_app.add_middleware.call_args
            assert "X-RateLimit-Limit" in call_args[1]["expose_headers"]
            assert "X-Request-ID" in call_args[1]["expose_headers"]

    def test_setup_cors_max_age(self, mock_app):
        """Test CORS setup with max age."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            setup_cors(mock_app, origins=["*"], max_age=3600)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["max_age"] == 3600

    def test_setup_cors_allow_credentials(self, mock_app):
        """Test CORS setup with credentials allowed."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            setup_cors(mock_app, origins=["*"], allow_credentials=True)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_credentials"] is True

    def test_setup_cors_import_error(self, mock_app):
        """Test handling of missing FastAPI."""
        with patch.dict("sys.modules", {"fastapi": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'fastapi'")):
                with pytest.raises(ImportError):
                    setup_cors(mock_app)


class TestGetCORSOriginsFromEnv:
    """Test getting CORS origins from environment."""

    def test_get_origins_from_env(self):
        """Test getting origins from environment variable."""
        with patch.dict(os.environ, {"CORS_ORIGINS": "https://a.com,https://b.com"}):
            origins = get_cors_origins_from_env()
            assert origins == ["https://a.com", "https://b.com"]

    def test_get_origins_from_env_with_spaces(self):
        """Test getting origins with extra spaces."""
        with patch.dict(os.environ, {"CORS_ORIGINS": " https://a.com , https://b.com "}):
            origins = get_cors_origins_from_env()
            assert origins == ["https://a.com", "https://b.com"]

    def test_get_origins_from_env_empty(self):
        """Test getting origins when env var is empty."""
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}, clear=True):
            origins = get_cors_origins_from_env()
            assert origins == []

    def test_get_origins_from_env_not_set(self):
        """Test getting origins when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            origins = get_cors_origins_from_env()
            assert origins == []

    def test_get_origins_with_default(self):
        """Test getting origins with default value."""
        with patch.dict(os.environ, {"CORS_ORIGINS": ""}, clear=True):
            default = ["https://default.com"]
            origins = get_cors_origins_from_env(default=default)
            assert origins == default

    def test_get_origins_custom_env_var(self):
        """Test getting origins from custom env var name."""
        with patch.dict(os.environ, {"MY_CORS": "https://custom.com"}):
            origins = get_cors_origins_from_env(env_var="MY_CORS")
            assert origins == ["https://custom.com"]


class TestCORSPresets:
    """Test CORS preset configurations."""

    @pytest.fixture
    def mock_app(self):
        """Create a mock FastAPI app."""
        app = MagicMock()
        app.add_middleware = MagicMock()
        return app

    def test_development_preset(self, mock_app):
        """Test development preset."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            CORSPresets.development(mock_app)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_origins"] == ["*"]

    def test_production_single_origin_preset(self, mock_app):
        """Test production single origin preset."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            CORSPresets.production_single_origin(mock_app, "https://app.example.com")

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_origins"] == ["https://app.example.com"]
            assert call_args[1]["allow_credentials"] is True

    def test_api_gateway_preset(self, mock_app):
        """Test API gateway preset."""
        origins = ["https://app.example.com", "https://admin.example.com"]

        with patch("fastapi.middleware.cors.CORSMiddleware"):
            CORSPresets.api_gateway(mock_app, origins)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_origins"] == origins
            assert "X-Total-Count" in call_args[1]["expose_headers"]
            assert "Link" in call_args[1]["expose_headers"]

    def test_public_api_preset(self, mock_app):
        """Test public API preset."""
        with patch("fastapi.middleware.cors.CORSMiddleware"):
            CORSPresets.public_api(mock_app)

            call_args = mock_app.add_middleware.call_args
            assert call_args[1]["allow_origins"] == ["*"]
            assert call_args[1]["allow_credentials"] is False
            assert call_args[1]["allow_methods"] == ["GET", "POST"]

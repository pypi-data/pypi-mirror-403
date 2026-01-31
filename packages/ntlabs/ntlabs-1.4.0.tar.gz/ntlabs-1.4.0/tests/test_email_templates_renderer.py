"""
Neural LAB Python SDK - Test Suite

Author: Anderson Henrique da Silva
Date: 2026-01-28
Location: Minas Gerais, Brasil
Copyright: Neural Thinker | AI Engineering LTDA

Description: Comprehensive tests for email template renderer
Version: 1.0.0
"""

import os
import tempfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from ntlabs.email.templates.renderer import (
    TemplateRenderer,
    get_builtin_templates,
    BASE_TEMPLATE,
    WELCOME_TEMPLATE,
    PASSWORD_RESET_TEMPLATE,
    NOTIFICATION_TEMPLATE,
)


class TestTemplateRendererInit:
    """Test TemplateRenderer initialization."""

    def test_default_init(self):
        """Test initialization with default values."""
        renderer = TemplateRenderer()
        assert renderer.template_dir is None
        assert renderer.auto_escape is True
        assert renderer.cache_enabled is True
        assert renderer._env is None

    def test_custom_init(self):
        """Test initialization with custom values."""
        renderer = TemplateRenderer(
            template_dir="/path/to/templates",
            auto_escape=False,
            cache_enabled=False,
        )
        assert renderer.template_dir == "/path/to/templates"
        assert renderer.auto_escape is False
        assert renderer.cache_enabled is False


class TestTemplateRendererEnvironment:
    """Test Jinja2 environment setup."""

    def test_get_env_without_directory(self):
        """Test getting environment without template directory."""
        renderer = TemplateRenderer()
        env = renderer._get_env()
        assert env is not None
        assert renderer._env is env  # Cached

    def test_get_env_with_directory(self):
        """Test getting environment with template directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TemplateRenderer(template_dir=tmpdir)
            env = renderer._get_env()
            assert env is not None
            assert env.loader is not None

    def test_get_env_import_error(self):
        """Test handling missing jinja2 package."""
        with patch.dict("sys.modules", {"jinja2": None}):
            renderer = TemplateRenderer()
            with pytest.raises(ImportError):
                renderer._get_env()


class TestTemplateRendererFilters:
    """Test custom Jinja2 filters."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer instance."""
        return TemplateRenderer()

    def test_currency_filter_brl(self, renderer):
        """Test BRL currency formatting."""
        env = renderer._get_env()
        template = env.from_string("{{ value | currency('BRL') }}")
        result = template.render(value=1234.56)
        assert "R$" in result
        assert "1.234,56" in result

    def test_currency_filter_usd(self, renderer):
        """Test USD currency formatting."""
        env = renderer._get_env()
        template = env.from_string("{{ value | currency('USD') }}")
        result = template.render(value=1234.56)
        assert "$" in result
        assert "1,234.56" in result

    def test_currency_filter_default(self, renderer):
        """Test default currency formatting."""
        env = renderer._get_env()
        template = env.from_string("{{ value | currency('EUR') }}")
        result = template.render(value=1234.56)
        assert "1,234.56" in result

    def test_date_filter(self, renderer):
        """Test date formatting filter."""
        env = renderer._get_env()
        template = env.from_string("{{ date | date }}")
        date = datetime(2026, 1, 28)
        result = template.render(date=date)
        assert "28/01/2026" in result

    def test_date_filter_custom_format(self, renderer):
        """Test date formatting with custom format."""
        env = renderer._get_env()
        template = env.from_string("{{ date | date('%Y-%m-%d') }}")
        date = datetime(2026, 1, 28)
        result = template.render(date=date)
        assert "2026-01-28" in result

    def test_datetime_filter(self, renderer):
        """Test datetime formatting filter."""
        env = renderer._get_env()
        template = env.from_string("{{ dt | datetime }}")
        dt = datetime(2026, 1, 28, 14, 30)
        result = template.render(dt=dt)
        assert "28/01/2026" in result
        assert "14:30" in result

    def test_phone_filter(self, renderer):
        """Test phone formatting filter."""
        with patch("ntlabs.validators.format_phone") as mock_format:
            mock_format.return_value = "(11) 98765-4321"
            env = renderer._get_env()
            template = env.from_string("{{ phone | phone }}")
            result = template.render(phone="11987654321")
            assert "(11) 98765-4321" in result

    def test_cpf_filter(self, renderer):
        """Test CPF formatting filter."""
        with patch("ntlabs.validators.format_cpf") as mock_format:
            mock_format.return_value = "123.456.789-09"
            env = renderer._get_env()
            template = env.from_string("{{ cpf | cpf }}")
            result = template.render(cpf="12345678909")
            assert "123.456.789-09" in result

    def test_cnpj_filter(self, renderer):
        """Test CNPJ formatting filter."""
        with patch("ntlabs.validators.format_cnpj") as mock_format:
            mock_format.return_value = "12.345.678/0001-90"
            env = renderer._get_env()
            template = env.from_string("{{ cnpj | cnpj }}")
            result = template.render(cnpj="12345678000190")
            assert "12.345.678/0001-90" in result


class TestTemplateRendererRender:
    """Test template rendering methods."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer instance."""
        return TemplateRenderer()

    def test_render_string(self, renderer):
        """Test rendering from string."""
        result = renderer.render_string(
            "Hello {{ name }}!",
            {"name": "World"},
        )
        assert result == "Hello World!"

    def test_render_string_with_filter(self, renderer):
        """Test rendering string with filter."""
        result = renderer.render_string(
            "Value: {{ num | currency('BRL') }}",
            {"num": 100},
        )
        assert "R$" in result
        assert "100,00" in result

    def test_render_inline(self, renderer):
        """Test inline rendering of subject and body."""
        subject, body = renderer.render_inline(
            subject_template="Hello {{ name }}",
            body_template="Welcome, {{ name }}!",
            context={"name": "User"},
        )
        assert subject == "Hello User"
        assert body == "Welcome, User!"

    def test_render_file_not_found(self, renderer):
        """Test rendering when template file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer_with_dir = TemplateRenderer(template_dir=tmpdir)
            with pytest.raises(Exception):  # jinja2.TemplateNotFound
                renderer_with_dir.render("nonexistent")


class TestBuiltinTemplates:
    """Test built-in templates."""

    @pytest.fixture
    def renderer(self):
        """Create a renderer instance."""
        return TemplateRenderer()

    def test_get_builtin_templates(self):
        """Test getting builtin templates dictionary."""
        templates = get_builtin_templates()
        assert "base.html" in templates
        assert "welcome.html" in templates
        assert "password_reset.html" in templates
        assert "notification.html" in templates

    def test_base_template_structure(self):
        """Test base template structure."""
        assert "<!DOCTYPE html>" in BASE_TEMPLATE
        assert "{% block content %}" in BASE_TEMPLATE
        assert "{% block header %}" in BASE_TEMPLATE
        assert "{% block footer %}" in BASE_TEMPLATE

    def test_welcome_template_extends_base(self):
        """Test welcome template extends base."""
        assert "{% extends" in WELCOME_TEMPLATE
        assert "user_name" in WELCOME_TEMPLATE
        assert "company_name" in WELCOME_TEMPLATE

    def test_password_reset_template(self):
        """Test password reset template."""
        assert "{% extends" in PASSWORD_RESET_TEMPLATE
        assert "reset_url" in PASSWORD_RESET_TEMPLATE
        assert "expires_in_hours" in PASSWORD_RESET_TEMPLATE

    def test_notification_template(self):
        """Test notification template."""
        assert "{% extends" in NOTIFICATION_TEMPLATE
        assert "title" in NOTIFICATION_TEMPLATE
        assert "message" in NOTIFICATION_TEMPLATE
        assert "action_url" in NOTIFICATION_TEMPLATE

    def test_render_welcome_template_from_string(self, renderer):
        """Test rendering welcome template from string."""
        result = renderer.render_string(
            WELCOME_TEMPLATE,
            {
                "user_name": "John",
                "company_name": "Acme Inc",
                "year": 2026,
            },
        )
        assert "John" in result
        assert "Acme Inc" in result

    def test_render_password_reset_template(self, renderer):
        """Test rendering password reset template."""
        result = renderer.render_string(
            PASSWORD_RESET_TEMPLATE,
            {
                "user_name": "Jane",
                "reset_url": "https://example.com/reset",
                "expires_in_hours": 24,
                "company_name": "Acme Inc",
                "year": 2026,
            },
        )
        assert "Jane" in result
        assert "https://example.com/reset" in result
        assert "24" in result

    def test_render_notification_template(self, renderer):
        """Test rendering notification template."""
        result = renderer.render_string(
            NOTIFICATION_TEMPLATE,
            {
                "title": "Important Notice",
                "message": "This is a notification",
                "company_name": "Acme Inc",
                "year": 2026,
            },
        )
        assert "Important Notice" in result
        assert "This is a notification" in result


class TestTemplateRendererWithFileSystem:
    """Test renderer with file system templates."""

    def test_render_from_file(self):
        """Test rendering from file system."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a template file
            template_path = os.path.join(tmpdir, "test.html")
            with open(template_path, "w") as f:
                f.write("Hello {{ name }}!")

            renderer = TemplateRenderer(template_dir=tmpdir)
            result = renderer.render("test", {"name": "World"})
            assert result == "Hello World!"

    def test_render_with_extension(self):
        """Test rendering with explicit extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, "test.txt")
            with open(template_path, "w") as f:
                f.write("Hello {{ name }}!")

            renderer = TemplateRenderer(template_dir=tmpdir)
            result = renderer.render("test", {"name": "World"}, extension=".txt")
            assert result == "Hello World!"

    def test_render_auto_adds_extension(self):
        """Test that extension is auto-added if not present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, "test.html")
            with open(template_path, "w") as f:
                f.write("Hello {{ name }}!")

            renderer = TemplateRenderer(template_dir=tmpdir)
            # Should work even without .html extension
            result = renderer.render("test.html", {"name": "World"})
            assert result == "Hello World!"


class TestTemplateRendererCaching:
    """Test template caching behavior."""

    def test_cache_enabled(self):
        """Test that caching is enabled by default."""
        renderer = TemplateRenderer(cache_enabled=True)
        env = renderer._get_env()
        assert env.auto_reload is False

    def test_cache_disabled(self):
        """Test disabling cache."""
        renderer = TemplateRenderer(cache_enabled=False)
        env = renderer._get_env()
        assert env.auto_reload is True

    def test_auto_escape_enabled(self):
        """Test auto escaping enabled."""
        renderer = TemplateRenderer(auto_escape=True)
        env = renderer._get_env()
        # Autoescape should be configured
        template = env.from_string("{{ html }}")
        result = template.render(html="<script>alert('xss')</script>")
        assert "&lt;" in result  # HTML escaped

    def test_auto_escape_disabled(self):
        """Test auto escaping disabled."""
        renderer = TemplateRenderer(auto_escape=False)
        env = renderer._get_env()
        template = env.from_string("{{ html }}")
        result = template.render(html="<b>Bold</b>")
        assert result == "<b>Bold</b>"  # Not escaped


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_render_empty_context(self):
        """Test rendering with empty context."""
        renderer = TemplateRenderer()
        result = renderer.render_string("Hello World!", {})
        assert result == "Hello World!"

    def test_render_missing_variable(self):
        """Test rendering with missing variable."""
        renderer = TemplateRenderer()
        result = renderer.render_string("Hello {{ name }}!", {})
        assert result == "Hello !"

    def test_render_complex_data(self):
        """Test rendering with complex data structures."""
        renderer = TemplateRenderer()
        template = """
        User: {{ user.name }}
        Items: {% for item in items %}{{ item }}{% if not loop.last %}, {% endif %}{% endfor %}
        """
        context = {
            "user": {"name": "John"},
            "items": ["a", "b", "c"],
        }
        result = renderer.render_string(template, context)
        assert "User: John" in result
        assert "Items: a, b, c" in result

    def test_render_conditional(self):
        """Test rendering with conditionals."""
        renderer = TemplateRenderer()
        template = "{% if show %}Visible{% else %}Hidden{% endif %}"

        result = renderer.render_string(template, {"show": True})
        assert result == "Visible"

        result = renderer.render_string(template, {"show": False})
        assert result == "Hidden"

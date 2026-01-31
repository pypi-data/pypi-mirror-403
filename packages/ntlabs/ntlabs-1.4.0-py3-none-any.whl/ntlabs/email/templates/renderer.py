"""
Email template rendering.

Provides template rendering using Jinja2 with email-specific
helpers and filters.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Jinja2-based email template renderer.

    Example:
        renderer = TemplateRenderer(template_dir="/path/to/templates")

        html = renderer.render("welcome", {
            "user_name": "John",
            "company_name": "Acme Inc"
        })
    """

    def __init__(
        self,
        template_dir: str | None = None,
        auto_escape: bool = True,
        cache_enabled: bool = True,
    ):
        """
        Initialize template renderer.

        Args:
            template_dir: Directory containing template files
            auto_escape: Enable HTML auto-escaping
            cache_enabled: Enable template caching
        """
        self.template_dir = template_dir
        self.auto_escape = auto_escape
        self.cache_enabled = cache_enabled
        self._env = None

    def _get_env(self):
        """Get or create Jinja2 environment."""
        if self._env is None:
            try:
                from jinja2 import Environment, FileSystemLoader, select_autoescape
            except ImportError as err:
                raise ImportError(
                    "jinja2 is required for template rendering. "
                    "Install it with: pip install jinja2"
                ) from err

            loader = None
            if self.template_dir:
                loader = FileSystemLoader(self.template_dir)

            self._env = Environment(
                loader=loader,
                autoescape=(
                    select_autoescape(["html", "xml"]) if self.auto_escape else False
                ),
                auto_reload=not self.cache_enabled,
            )

            # Add custom filters
            self._add_filters()

        return self._env

    def _add_filters(self):
        """Add custom Jinja2 filters."""
        env = self._env

        # Currency formatting
        def format_currency(value, currency="BRL"):
            if currency == "BRL":
                return (
                    f"R$ {value:,.2f}".replace(",", "X")
                    .replace(".", ",")
                    .replace("X", ".")
                )
            elif currency == "USD":
                return f"$ {value:,.2f}"
            return f"{value:,.2f}"

        # Date formatting
        def format_date(value, fmt="%d/%m/%Y"):
            if hasattr(value, "strftime"):
                return value.strftime(fmt)
            return str(value)

        # Date/time formatting
        def format_datetime(value, fmt="%d/%m/%Y %H:%M"):
            if hasattr(value, "strftime"):
                return value.strftime(fmt)
            return str(value)

        # Phone formatting
        def format_phone(value):
            from ntlabs.validators import format_phone as _format_phone

            return _format_phone(str(value))

        # CPF formatting
        def format_cpf(value):
            from ntlabs.validators import format_cpf as _format_cpf

            return _format_cpf(str(value))

        # CNPJ formatting
        def format_cnpj(value):
            from ntlabs.validators import format_cnpj as _format_cnpj

            return _format_cnpj(str(value))

        env.filters["currency"] = format_currency
        env.filters["date"] = format_date
        env.filters["datetime"] = format_datetime
        env.filters["phone"] = format_phone
        env.filters["cpf"] = format_cpf
        env.filters["cnpj"] = format_cnpj

    def render(
        self, template_name: str, context: dict[str, Any], extension: str = ".html"
    ) -> str:
        """
        Render a template file.

        Args:
            template_name: Template name (without extension)
            context: Template variables
            extension: File extension (default .html)

        Returns:
            Rendered template string
        """
        env = self._get_env()

        if not template_name.endswith(extension):
            template_name = f"{template_name}{extension}"

        template = env.get_template(template_name)
        return template.render(**context)

    def render_string(self, template_string: str, context: dict[str, Any]) -> str:
        """
        Render a template from string.

        Args:
            template_string: Template content as string
            context: Template variables

        Returns:
            Rendered string
        """
        env = self._get_env()
        template = env.from_string(template_string)
        return template.render(**context)

    def render_inline(
        self, subject_template: str, body_template: str, context: dict[str, Any]
    ) -> tuple[str, str]:
        """
        Render subject and body templates.

        Args:
            subject_template: Subject template string
            body_template: Body template string
            context: Template variables

        Returns:
            Tuple of (rendered_subject, rendered_body)
        """
        subject = self.render_string(subject_template, context)
        body = self.render_string(body_template, context)
        return subject, body


# =============================================================================
# Built-in Templates
# =============================================================================

BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ subject }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid #eee;
        }
        .content {
            padding: 30px 0;
        }
        .footer {
            text-align: center;
            padding: 20px 0;
            border-top: 1px solid #eee;
            font-size: 12px;
            color: #666;
        }
        .button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 10px 0;
        }
        .button:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    {% block header %}
    <div class="header">
        {% if logo_url %}
        <img src="{{ logo_url }}" alt="{{ company_name }}" style="max-height: 50px;">
        {% else %}
        <h1>{{ company_name }}</h1>
        {% endif %}
    </div>
    {% endblock %}

    <div class="content">
        {% block content %}{% endblock %}
    </div>

    {% block footer %}
    <div class="footer">
        <p>&copy; {{ year }} {{ company_name }}. Todos os direitos reservados.</p>
        {% if unsubscribe_url %}
        <p><a href="{{ unsubscribe_url }}">Cancelar inscrição</a></p>
        {% endif %}
    </div>
    {% endblock %}
</body>
</html>
"""

WELCOME_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>Bem-vindo(a), {{ user_name }}!</h2>
<p>Obrigado por se cadastrar em {{ company_name }}.</p>
<p>Sua conta foi criada com sucesso. Você já pode começar a usar nossos serviços.</p>
{% if action_url %}
<p style="text-align: center;">
    <a href="{{ action_url }}" class="button">Acessar Minha Conta</a>
</p>
{% endif %}
<p>Se você não criou esta conta, por favor ignore este email.</p>
{% endblock %}
"""

PASSWORD_RESET_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>Redefinição de Senha</h2>
<p>Olá, {{ user_name }}.</p>
<p>Recebemos uma solicitação para redefinir a senha da sua conta.</p>
<p style="text-align: center;">
    <a href="{{ reset_url }}" class="button">Redefinir Senha</a>
</p>
<p>Este link expira em {{ expires_in_hours }} horas.</p>
<p>Se você não solicitou essa alteração, pode ignorar este email com segurança.</p>
{% endblock %}
"""

NOTIFICATION_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>{{ title }}</h2>
<p>{{ message }}</p>
{% if action_url %}
<p style="text-align: center;">
    <a href="{{ action_url }}" class="button">{{ action_text|default("Ver Detalhes") }}</a>
</p>
{% endif %}
{% endblock %}
"""


def get_builtin_templates() -> dict[str, str]:
    """Get dictionary of built-in templates."""
    return {
        "base.html": BASE_TEMPLATE,
        "welcome.html": WELCOME_TEMPLATE,
        "password_reset.html": PASSWORD_RESET_TEMPLATE,
        "notification.html": NOTIFICATION_TEMPLATE,
    }

"""
Sentry integration for error tracking.

Provides simplified Sentry setup for Python applications.
"""

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def setup_sentry(
    dsn: str,
    environment: str = "production",
    release: str | None = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
    send_default_pii: bool = False,
    integrations: list[Any] | None = None,
    ignore_errors: list[type] | None = None,
    before_send: Callable | None = None,
    debug: bool = False,
    **kwargs,
) -> bool:
    """
    Initialize Sentry error tracking.

    Args:
        dsn: Sentry DSN (Data Source Name)
        environment: Environment name (production, staging, development)
        release: Application release/version
        traces_sample_rate: Percentage of transactions to capture (0.0 - 1.0)
        profiles_sample_rate: Percentage of transactions to profile (0.0 - 1.0)
        send_default_pii: Send personally identifiable information
        integrations: Additional Sentry integrations
        ignore_errors: Exception types to ignore
        before_send: Callback to process events before sending
        debug: Enable Sentry debug mode
        **kwargs: Additional Sentry SDK options

    Returns:
        True if Sentry was initialized successfully

    Example:
        from ntlabs.observability import setup_sentry

        setup_sentry(
            dsn="https://xxx@sentry.io/123",
            environment="production",
            release="1.0.0",
            traces_sample_rate=0.1,
        )
    """
    if not dsn:
        logger.warning("Sentry DSN not provided, skipping initialization")
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration
    except ImportError:
        logger.warning(
            "sentry-sdk package not installed. "
            "Install it with: pip install sentry-sdk"
        )
        return False

    # Default integrations
    default_integrations = [
        LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        ),
    ]

    # Try to add FastAPI integration
    try:
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        default_integrations.extend(
            [
                FastApiIntegration(),
                StarletteIntegration(),
            ]
        )
    except ImportError:
        pass

    # Try to add HTTPX integration
    try:
        from sentry_sdk.integrations.httpx import HttpxIntegration

        default_integrations.append(HttpxIntegration())
    except ImportError:
        pass

    # Try to add Redis integration
    try:
        from sentry_sdk.integrations.redis import RedisIntegration

        default_integrations.append(RedisIntegration())
    except ImportError:
        pass

    # Combine integrations
    all_integrations = default_integrations + (integrations or [])

    # Build ignore list
    ignore_list = ignore_errors or []

    def _before_send(event, hint):
        # Check if we should ignore this error
        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]
            if exc_type in ignore_list:
                return None

        # Call custom before_send if provided
        if before_send:
            return before_send(event, hint)

        return event

    # Initialize Sentry
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        traces_sample_rate=traces_sample_rate,
        profiles_sample_rate=profiles_sample_rate,
        send_default_pii=send_default_pii,
        integrations=all_integrations,
        before_send=_before_send,
        debug=debug,
        **kwargs,
    )

    logger.info(f"Sentry initialized: environment={environment}")
    return True


def capture_exception(
    error: Exception,
    extra: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
    user: dict[str, Any] | None = None,
    level: str = "error",
) -> str | None:
    """
    Capture an exception to Sentry.

    Args:
        error: Exception to capture
        extra: Additional context data
        tags: Tags to attach to the event
        user: User information
        level: Error level (error, warning, info)

    Returns:
        Event ID or None if capture failed

    Example:
        try:
            risky_operation()
        except Exception as e:
            capture_exception(
                e,
                extra={"operation": "risky_operation"},
                tags={"component": "payment"},
            )
    """
    try:
        import sentry_sdk
        from sentry_sdk import set_extra, set_level, set_tag, set_user

        # Set context
        if user:
            set_user(user)

        if tags:
            for key, value in tags.items():
                set_tag(key, value)

        if extra:
            for key, value in extra.items():
                set_extra(key, value)

        set_level(level)

        # Capture
        event_id = sentry_sdk.capture_exception(error)
        return event_id

    except ImportError:
        logger.error(f"Sentry not available: {error}")
        return None


def capture_message(
    message: str,
    level: str = "info",
    extra: dict[str, Any] | None = None,
    tags: dict[str, str] | None = None,
) -> str | None:
    """
    Capture a message to Sentry.

    Args:
        message: Message to capture
        level: Message level (error, warning, info, debug)
        extra: Additional context data
        tags: Tags to attach

    Returns:
        Event ID or None
    """
    try:
        import sentry_sdk
        from sentry_sdk import set_extra, set_tag

        if tags:
            for key, value in tags.items():
                set_tag(key, value)

        if extra:
            for key, value in extra.items():
                set_extra(key, value)

        return sentry_sdk.capture_message(message, level=level)

    except ImportError:
        logger.info(f"Sentry message: {message}")
        return None


def set_user_context(
    user_id: str | None = None,
    email: str | None = None,
    username: str | None = None,
    ip_address: str | None = None,
    **kwargs,
) -> None:
    """
    Set user context for Sentry events.

    Args:
        user_id: User ID
        email: User email
        username: Username
        ip_address: User IP address
        **kwargs: Additional user data
    """
    try:
        import sentry_sdk

        user_data = {}
        if user_id:
            user_data["id"] = user_id
        if email:
            user_data["email"] = email
        if username:
            user_data["username"] = username
        if ip_address:
            user_data["ip_address"] = ip_address
        user_data.update(kwargs)

        if user_data:
            sentry_sdk.set_user(user_data)

    except ImportError:
        pass


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """
    Add a breadcrumb for debugging.

    Breadcrumbs are a trail of events that led up to an error.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "http", "query", "auth")
        level: Level (debug, info, warning, error, critical)
        data: Additional data
    """
    try:
        import sentry_sdk

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data,
        )

    except ImportError:
        pass

"""
Request logging middleware for FastAPI.

Provides structured logging for HTTP requests and responses.
"""

import logging
import time
import uuid

logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """
    Middleware for logging HTTP requests and responses.

    Logs request details including:
    - Request ID
    - Method and path
    - Client IP
    - Response status
    - Duration
    - User agent

    Example:
        from fastapi import FastAPI
        from ntlabs.middleware import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        # With custom logger
        import logging
        app.add_middleware(
            LoggingMiddleware,
            logger=logging.getLogger("api"),
            log_request_body=True,
        )
    """

    def __init__(
        self,
        app,
        logger: logging.Logger | None = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_length: int = 1000,
        exclude_paths: list[str] | None = None,
        exclude_headers: list[str] | None = None,
        request_id_header: str = "X-Request-ID",
        generate_request_id: bool = True,
        slow_request_threshold: float = 1.0,  # seconds
    ):
        """
        Initialize logging middleware.

        Args:
            app: ASGI application
            logger: Logger instance (uses default if not provided)
            log_request_body: Log request body (be careful with sensitive data)
            log_response_body: Log response body
            max_body_length: Maximum body length to log
            exclude_paths: Paths to exclude from logging
            exclude_headers: Headers to exclude from logging
            request_id_header: Header name for request ID
            generate_request_id: Generate request ID if not provided
            slow_request_threshold: Log slow requests above this threshold
        """
        self.app = app
        self.logger = logger or logging.getLogger("ntlabs.api")
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_length = max_body_length
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.exclude_headers = {
            h.lower()
            for h in (exclude_headers or ["authorization", "cookie", "x-api-key"])
        }
        self.request_id_header = request_id_header
        self.generate_request_id = generate_request_id
        self.slow_request_threshold = slow_request_threshold

    async def __call__(self, scope, receive, send):
        """ASGI middleware handler."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Skip excluded paths
        if any(path.startswith(p) for p in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # Extract request info
        method = scope.get("method", "")
        headers = dict(scope.get("headers", []))

        # Get or generate request ID
        request_id = headers.get(self.request_id_header.lower().encode(), b"").decode()

        if not request_id and self.generate_request_id:
            request_id = str(uuid.uuid4())[:8]

        # Get client IP
        client_ip = self._get_client_ip(scope, headers)

        # Start timing
        start_time = time.perf_counter()

        # Variables to capture response
        status_code = 500
        response_headers = {}

        async def send_wrapper(message):
            nonlocal status_code, response_headers

            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                response_headers = dict(message.get("headers", []))

                # Add request ID to response
                if request_id:
                    existing = list(message.get("headers", []))
                    existing.append(
                        (self.request_id_header.encode(), request_id.encode())
                    )
                    message["headers"] = existing

            await send(message)

        # Process request
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log exception
            duration = time.perf_counter() - start_time
            self._log_request(
                request_id=request_id,
                method=method,
                path=path,
                client_ip=client_ip,
                status_code=500,
                duration=duration,
                error=str(e),
            )
            raise

        # Calculate duration
        duration = time.perf_counter() - start_time

        # Log request
        self._log_request(
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client_ip,
            status_code=status_code,
            duration=duration,
        )

    def _get_client_ip(self, scope, headers) -> str:
        """Extract client IP from request."""
        # Check forwarded headers
        forwarded = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = headers.get(b"x-real-ip", b"").decode()
        if real_ip:
            return real_ip

        # Fall back to direct client
        client = scope.get("client")
        if client:
            return client[0]

        return "unknown"

    def _log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        client_ip: str,
        status_code: int,
        duration: float,
        error: str | None = None,
    ):
        """Log request details."""
        duration_ms = round(duration * 1000, 2)

        # Build log message
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "client_ip": client_ip,
            "status": status_code,
            "duration_ms": duration_ms,
        }

        if error:
            log_data["error"] = error

        # Determine log level
        if error or status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        elif duration > self.slow_request_threshold:
            level = logging.WARNING
            log_data["slow_request"] = True
        else:
            level = logging.INFO

        # Format message
        message = (
            f"{method} {path} - {status_code} - {duration_ms}ms "
            f"[{request_id}] ({client_ip})"
        )

        self.logger.log(level, message, extra=log_data)


def get_request_id() -> str | None:
    """
    Get current request ID from context.

    Note: This requires contextvars support in your application.

    Returns:
        Current request ID or None
    """
    # This is a placeholder - actual implementation would use contextvars
    return None


class StructuredLogger:
    """
    Structured logger wrapper for consistent log formatting.

    Example:
        logger = StructuredLogger("api")
        logger.info("User logged in", user_id="123", action="login")
    """

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **kwargs):
        """Log with structured data."""
        extra = {"structured_data": kwargs} if kwargs else {}
        self._logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)

"""
Audit logging for tracking user actions and system events.

Provides structured audit logging with:
- Supabase storage integration
- Severity levels
- Action categorization
- User and IP tracking
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AuditSeverity(Enum):
    """Audit log severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """Audit log categories."""

    AUTH = "auth"  # Login, logout, password changes
    DATA = "data"  # CRUD operations
    ADMIN = "admin"  # Administrative actions
    SECURITY = "security"  # Security-related events
    SYSTEM = "system"  # System events
    API = "api"  # API calls


@dataclass
class AuditEntry:
    """Audit log entry."""

    action: str
    category: AuditCategory
    severity: AuditSeverity
    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        data = {
            "action": self.action,
            "category": self.category.value,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }
        return {k: v for k, v in data.items() if v is not None}


class AuditLogger:
    """
    Audit logger with Supabase storage.

    Example:
        audit = AuditLogger(
            service="hipocrates-api",
            supabase_url="https://xxx.supabase.co",
            supabase_key="xxx",
        )

        # Log user login
        await audit.log(
            action="user_login",
            category=AuditCategory.AUTH,
            user_id="user_123",
            ip_address="192.168.1.1",
            details={"method": "oauth", "provider": "google"},
        )

        # Log data access
        await audit.log(
            action="view_patient_record",
            category=AuditCategory.DATA,
            user_id="doctor_456",
            resource_type="patient",
            resource_id="patient_789",
            severity=AuditSeverity.INFO,
        )
    """

    def __init__(
        self,
        service: str,
        supabase_url: str | None = None,
        supabase_key: str | None = None,
        table_name: str = "audit_logs",
        buffer_size: int = 100,
        flush_interval: float = 5.0,
        enable_local_logging: bool = True,
    ):
        """
        Initialize audit logger.

        Args:
            service: Service/application name
            supabase_url: Supabase project URL
            supabase_key: Supabase service key
            table_name: Table name for audit logs
            buffer_size: Buffer size before auto-flush
            flush_interval: Flush interval in seconds
            enable_local_logging: Also log to Python logger
        """
        self.service = service
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.table_name = table_name
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.enable_local_logging = enable_local_logging

        self._buffer: list[AuditEntry] = []
        self._client = None

    async def _get_client(self):
        """Get or create Supabase client."""
        if self._client is None and self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client

                self._client = create_client(self.supabase_url, self.supabase_key)
            except ImportError:
                logger.warning(
                    "supabase package not installed. Audit logs will only be "
                    "written to local logger."
                )
        return self._client

    async def log(
        self,
        action: str,
        category: AuditCategory = AuditCategory.SYSTEM,
        severity: AuditSeverity = AuditSeverity.INFO,
        user_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Log an audit entry.

        Args:
            action: Action name (e.g., "user_login", "record_updated")
            category: Audit category
            severity: Log severity
            user_id: User who performed the action
            ip_address: Client IP address
            user_agent: Client user agent
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Action details
            metadata: Additional metadata
        """
        entry = AuditEntry(
            action=action,
            category=category,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            metadata={**(metadata or {}), "service": self.service},
        )

        # Log locally
        if self.enable_local_logging:
            self._log_local(entry)

        # Buffer for Supabase
        self._buffer.append(entry)

        # Auto-flush if buffer is full
        if len(self._buffer) >= self.buffer_size:
            await self.flush()

    def _log_local(self, entry: AuditEntry) -> None:
        """Log entry to Python logger."""
        level_map = {
            AuditSeverity.DEBUG: logging.DEBUG,
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }

        level = level_map.get(entry.severity, logging.INFO)

        message = (
            f"[AUDIT] {entry.action} | "
            f"category={entry.category.value} | "
            f"user={entry.user_id or 'anonymous'} | "
            f"ip={entry.ip_address or 'unknown'}"
        )

        if entry.resource_type:
            message += f" | resource={entry.resource_type}:{entry.resource_id}"

        logger.log(level, message, extra={"audit": entry.to_dict()})

    async def flush(self) -> int:
        """
        Flush buffered entries to Supabase.

        Returns:
            Number of entries flushed
        """
        if not self._buffer:
            return 0

        entries = self._buffer.copy()
        self._buffer.clear()

        client = await self._get_client()
        if not client:
            return 0

        try:
            # Insert to Supabase
            data = [entry.to_dict() for entry in entries]
            client.table(self.table_name).insert(data).execute()
            return len(entries)

        except Exception as e:
            logger.error(f"Failed to flush audit logs: {e}")
            # Re-add to buffer
            self._buffer.extend(entries)
            return 0

    # Convenience methods
    async def log_auth(
        self,
        action: str,
        user_id: str | None = None,
        ip_address: str | None = None,
        success: bool = True,
        **kwargs,
    ):
        """Log authentication event."""
        await self.log(
            action=action,
            category=AuditCategory.AUTH,
            severity=AuditSeverity.INFO if success else AuditSeverity.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            details={"success": success, **kwargs},
        )

    async def log_data_access(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str | None = None,
        **kwargs,
    ):
        """Log data access event."""
        await self.log(
            action=action,
            category=AuditCategory.DATA,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=kwargs,
        )

    async def log_security(
        self,
        action: str,
        severity: AuditSeverity = AuditSeverity.WARNING,
        user_id: str | None = None,
        ip_address: str | None = None,
        **kwargs,
    ):
        """Log security event."""
        await self.log(
            action=action,
            category=AuditCategory.SECURITY,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            details=kwargs,
        )

    async def close(self):
        """Flush remaining entries and close."""
        await self.flush()

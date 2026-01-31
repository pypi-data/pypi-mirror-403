"""
Common schemas used across the API.

Provides reusable schemas for common patterns.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class TimestampMixin(BaseModel):
    """
    Mixin for timestamp fields.

    Add to models that need created_at/updated_at tracking.
    """

    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


class SoftDeleteMixin(BaseModel):
    """
    Mixin for soft delete support.

    Add to models that use soft deletion instead of hard delete.
    """

    deleted_at: datetime | None = Field(None, description="Deletion timestamp")
    is_deleted: bool = Field(default=False, description="Soft delete flag")


class MetadataMixin(BaseModel):
    """
    Mixin for metadata field.

    Add to models that need arbitrary metadata storage.
    """

    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class HealthResponse(BaseModel):
    """
    Health check response.

    Standard format for /health endpoints.
    """

    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    version: str | None = Field(None, description="Service version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Check timestamp"
    )
    checks: dict[str, Any] | None = Field(None, description="Individual health checks")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-01-27T12:00:00Z",
                "checks": {
                    "database": {"status": "healthy", "latency_ms": 5},
                    "redis": {"status": "healthy", "latency_ms": 2},
                },
            }
        }
    }


class SuccessResponse(BaseModel):
    """
    Generic success response.

    Use for operations that don't return specific data.
    """

    success: bool = Field(default=True, description="Operation succeeded")
    message: str = Field(
        default="Operation completed successfully", description="Success message"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "User deleted successfully",
            }
        }
    }


class DataResponse(BaseModel, Generic[T]):
    """
    Generic data wrapper response.

    Wraps data in a consistent envelope format.
    """

    data: T = Field(..., description="Response data")
    message: str | None = Field(None, description="Optional message")

    model_config = {
        "json_schema_extra": {
            "example": {
                "data": {"id": "123", "name": "Example"},
                "message": "Data retrieved successfully",
            }
        }
    }


class CountResponse(BaseModel):
    """
    Count response for aggregate queries.
    """

    count: int = Field(..., ge=0, description="Item count")

    model_config = {
        "json_schema_extra": {
            "example": {
                "count": 42,
            }
        }
    }


class IdResponse(BaseModel):
    """
    Response containing just an ID.

    Useful for create operations.
    """

    id: str = Field(..., description="Created resource ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "res_abc123",
            }
        }
    }


class BulkOperationResponse(BaseModel):
    """
    Response for bulk operations.
    """

    total: int = Field(..., description="Total items processed")
    succeeded: int = Field(..., description="Successfully processed")
    failed: int = Field(..., description="Failed items")
    errors: list | None = Field(None, description="Error details for failed items")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 100,
                "succeeded": 98,
                "failed": 2,
                "errors": [
                    {"index": 5, "error": "Invalid email format"},
                    {"index": 42, "error": "Duplicate entry"},
                ],
            }
        }
    }


class FileUploadResponse(BaseModel):
    """
    Response for file upload operations.
    """

    file_id: str = Field(..., description="Uploaded file ID")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    url: str | None = Field(None, description="File URL")

    model_config = {
        "json_schema_extra": {
            "example": {
                "file_id": "file_abc123",
                "filename": "document.pdf",
                "size": 102400,
                "content_type": "application/pdf",
                "url": "https://storage.example.com/files/document.pdf",
            }
        }
    }


class WebhookPayload(BaseModel):
    """
    Standard webhook payload format.
    """

    event: str = Field(..., description="Event type")
    data: dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    webhook_id: str | None = Field(None, description="Webhook delivery ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "event": "user.created",
                "data": {"user_id": "user_123", "email": "user@example.com"},
                "timestamp": "2026-01-27T12:00:00Z",
                "webhook_id": "wh_abc123",
            }
        }
    }


class Address(BaseModel):
    """
    Standard address schema.
    """

    street: str = Field(..., description="Street address")
    number: str | None = Field(None, description="Street number")
    complement: str | None = Field(None, description="Address complement")
    neighborhood: str | None = Field(None, description="Neighborhood")
    city: str = Field(..., description="City")
    state: str = Field(..., min_length=2, max_length=2, description="State code (UF)")
    postal_code: str = Field(..., description="Postal code (CEP)")
    country: str = Field(default="BR", description="Country code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "street": "Av. Paulista",
                "number": "1000",
                "complement": "Sala 101",
                "neighborhood": "Bela Vista",
                "city": "São Paulo",
                "state": "SP",
                "postal_code": "01310-100",
                "country": "BR",
            }
        }
    }


class ContactInfo(BaseModel):
    """
    Standard contact information schema.
    """

    email: str | None = Field(None, description="Email address")
    phone: str | None = Field(None, description="Phone number")
    mobile: str | None = Field(None, description="Mobile number")
    whatsapp: str | None = Field(None, description="WhatsApp number")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "contact@example.com",
                "phone": "(11) 3333-4444",
                "mobile": "(11) 99999-8888",
                "whatsapp": "(11) 99999-8888",
            }
        }
    }

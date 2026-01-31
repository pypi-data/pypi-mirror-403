"""
Pagination schemas for list responses.

Provides generic pagination wrappers for API responses.
"""

from math import ceil
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Pagination parameters for requests.

    Example:
        @router.get("/users")
        async def list_users(pagination: PaginationParams = Depends()):
            ...
    """

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(None, description="Field to sort by")
    sort_order: str = Field(
        default="asc", pattern="^(asc|desc)$", description="Sort order"
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database queries."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response.

    Example:
        @router.get("/users", response_model=PaginatedResponse[UserResponse])
        async def list_users(page: int = 1, page_size: int = 20):
            users = await db.get_users(page, page_size)
            total = await db.count_users()
            return PaginatedResponse(
                items=users,
                total=total,
                page=page,
                page_size=page_size,
            )
    """

    items: list[T] = Field(..., description="Page items")
    total: int = Field(..., ge=0, description="Total item count")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        return ceil(self.total / self.page_size) if self.page_size > 0 else 0

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}],
                "total": 50,
                "page": 1,
                "page_size": 20,
            }
        }
    }


class PaginatedResponseWithMeta(PaginatedResponse[T], Generic[T]):
    """
    Paginated response with additional metadata.

    Includes navigation info in the response.
    """

    total_pages: int = Field(default=0, description="Total pages")
    has_next: bool = Field(default=False, description="Has next page")
    has_prev: bool = Field(default=False, description="Has previous page")
    next_page: int | None = Field(None, description="Next page number")
    prev_page: int | None = Field(None, description="Previous page number")

    def __init__(self, **data):
        # Calculate meta fields before validation
        if "total" in data and "page_size" in data:
            total_pages = ceil(data["total"] / data["page_size"])
            data["total_pages"] = total_pages

            page = data.get("page", 1)
            data["has_next"] = page < total_pages
            data["has_prev"] = page > 1
            data["next_page"] = page + 1 if page < total_pages else None
            data["prev_page"] = page - 1 if page > 1 else None

        super().__init__(**data)

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [{"id": "1", "name": "Item 1"}],
                "total": 50,
                "page": 2,
                "page_size": 20,
                "total_pages": 3,
                "has_next": True,
                "has_prev": True,
                "next_page": 3,
                "prev_page": 1,
            }
        }
    }


class CursorPaginationParams(BaseModel):
    """
    Cursor-based pagination parameters.

    Better for large datasets and real-time data.
    """

    cursor: str | None = Field(None, description="Cursor for next page")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """
    Cursor-based paginated response.

    Example:
        @router.get("/events", response_model=CursorPaginatedResponse[EventResponse])
        async def list_events(cursor: str = None, limit: int = 20):
            events, next_cursor = await db.get_events_after(cursor, limit)
            return CursorPaginatedResponse(
                items=events,
                next_cursor=next_cursor,
                has_more=next_cursor is not None,
            )
    """

    items: list[T] = Field(..., description="Page items")
    next_cursor: str | None = Field(None, description="Cursor for next page")
    prev_cursor: str | None = Field(None, description="Cursor for previous page")
    has_more: bool = Field(..., description="More items available")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [{"id": "1", "name": "Item 1"}],
                "next_cursor": "eyJpZCI6IjEwMCJ9",
                "prev_cursor": None,
                "has_more": True,
            }
        }
    }


def paginate_list(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
) -> PaginatedResponse:
    """
    Helper to create paginated response from list.

    Args:
        items: Items for current page
        total: Total item count
        page: Current page number
        page_size: Items per page

    Returns:
        PaginatedResponse
    """
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )

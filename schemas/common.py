"""
Common Pydantic Schemas

Provides base schemas and standard response formats used across all endpoints.
"""
from typing import Generic, TypeVar, Optional, Any, List
from pydantic import BaseModel, Field


# Generic type for data payload
T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response format."""
    success: bool = Field(default=True, description="Indicates the request was successful")
    message: str = Field(description="Human-readable success message")
    data: Optional[T] = Field(default=None, description="Response data payload")
    meta: Optional[dict] = Field(default=None, description="Additional metadata (pagination, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Request completed successfully",
                "data": {},
                "meta": None
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = Field(default=False, description="Indicates the request failed")
    message: str = Field(description="Human-readable error message")
    error_code: str = Field(description="Machine-readable error identifier")
    details: Optional[Any] = Field(default=None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Resource not found",
                "error_code": "NOT_FOUND",
                "details": None
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int = Field(description="Current page number (1-indexed)")
    per_page: int = Field(description="Number of items per page")
    total: int = Field(description="Total number of items")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "per_page": 20,
                "total": 100,
                "total_pages": 5,
                "has_next": True,
                "has_prev": False
            }
        }


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response format."""
    success: bool = Field(default=True)
    message: str = Field(default="Data retrieved successfully")
    data: List[T] = Field(description="List of items for the current page")
    meta: PaginationMeta = Field(description="Pagination metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Data retrieved successfully",
                "data": [],
                "meta": {
                    "page": 1,
                    "per_page": 20,
                    "total": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }


class IdResponse(BaseModel):
    """Response with created/updated resource ID."""
    success: bool = Field(default=True)
    message: str = Field(description="Success message")
    data: dict = Field(description="Dictionary containing the resource ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Resource created successfully",
                "data": {"id": 123}
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Server status (ok/error)")
    message: str = Field(description="Status message")
    framework: str = Field(default="FastAPI")
    database: Optional[str] = Field(default=None, description="Database connection status")
    version: Optional[str] = Field(default=None, description="Application version")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "Server is running",
                "framework": "FastAPI",
                "database": "connected",
                "version": "2.0.0"
            }
        }


class BulkOperationResponse(BaseModel):
    """Response for bulk operations (create, update, delete)."""
    success: bool = Field(default=True)
    message: str = Field(description="Operation summary message")
    data: dict = Field(description="Operation statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Bulk operation completed",
                "data": {
                    "total": 100,
                    "succeeded": 95,
                    "failed": 5,
                    "errors": []
                }
            }
        }

"""
Pydantic Schemas for Error Responses

Defines standardized error response formats.
"""
from typing import Any, Optional, List
from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """Single validation error detail."""
    field: str = Field(description="Field path that failed validation")
    message: str = Field(description="Validation error message")
    type: str = Field(description="Error type identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "body.num_topics",
                "message": "ensure this value is greater than 0",
                "type": "greater_than"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""
    success: bool = Field(default=False, description="Always false for errors")
    message: str = Field(default="Validation failed. Please check your input.")
    error_code: str = Field(default="VALIDATION_ERROR")
    details: List[ValidationErrorDetail] = Field(description="List of validation errors")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Validation failed. Please check your input.",
                "error_code": "VALIDATION_ERROR",
                "details": [
                    {
                        "field": "body.num_topics",
                        "message": "ensure this value is greater than 0",
                        "type": "greater_than"
                    }
                ]
            }
        }


class StandardErrorResponse(BaseModel):
    """Standard error response format."""
    success: bool = Field(default=False, description="Always false for errors")
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


class DatabaseErrorResponse(BaseModel):
    """Response for database errors."""
    success: bool = Field(default=False)
    message: str = Field(description="Database error message")
    error_code: str = Field(default="DATABASE_ERROR")
    details: Optional[str] = Field(default=None, description="Technical error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Failed to execute database query",
                "error_code": "DATABASE_ERROR",
                "details": None
            }
        }


class PipelineErrorResponse(BaseModel):
    """Response for pipeline errors."""
    success: bool = Field(default=False)
    message: str = Field(description="Pipeline error message")
    error_code: str = Field(default="PIPELINE_ERROR")
    details: Optional[dict] = Field(
        default=None,
        description="Additional error context including stage, error type, etc."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Pipeline error at crawling: Failed to fetch URL",
                "error_code": "PIPELINE_ERROR",
                "details": {
                    "stage": "crawling",
                    "url": "https://example.com/article",
                    "error_type": "ConnectionError"
                }
            }
        }


class AuthenticationErrorResponse(BaseModel):
    """Response for authentication errors."""
    success: bool = Field(default=False)
    message: str = Field(description="Authentication error message")
    error_code: str = Field(default="UNAUTHORIZED")
    details: Optional[dict] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Invalid or expired token",
                "error_code": "UNAUTHORIZED",
                "details": None
            }
        }


class NotFoundErrorResponse(BaseModel):
    """Response for resource not found errors."""
    success: bool = Field(default=False)
    message: str = Field(description="Not found error message")
    error_code: str = Field(default="NOT_FOUND")
    details: Optional[dict] = Field(
        default=None,
        description="Resource type and identifier"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "message": "Project not found: 123",
                "error_code": "NOT_FOUND",
                "details": {
                    "resource_type": "Project",
                    "identifier": 123
                }
            }
        }

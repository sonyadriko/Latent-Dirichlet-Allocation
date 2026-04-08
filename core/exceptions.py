"""
Custom Exception Classes for LDA Application

Provides standardized exception handling with error codes and HTTP status mapping.
"""
from typing import Any, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """
    Base exception class for all application errors.

    Provides standardized error response format with:
    - message: Human-readable error description
    - error_code: Machine-readable error identifier
    - status_code: HTTP status code
    - details: Additional error context (optional)
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None
    ):
        self.error_code = error_code
        self.details = details
        super().__init__(status_code=status_code, detail=message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response."""
        return {
            'success': False,
            'message': self.detail,
            'error_code': self.error_code,
            'details': self.details
        }


class NotFoundException(AppException):
    """Resource not found exception (404)."""

    def __init__(self, resource: str, identifier: Optional[Any] = None):
        message = f"{resource} not found"
        if identifier is not None:
            message += f": {identifier}"
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )


class ValidationException(AppException):
    """Input validation failed exception (400)."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class UnauthorizedException(AppException):
    """Authentication required exception (401)."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(AppException):
    """Access denied exception (403)."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN
        )


class ConflictException(AppException):
    """Resource conflict exception (409)."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class PipelineException(AppException):
    """KDD Pipeline error exception (422)."""

    def __init__(self, message: str, stage: Optional[str] = None, details: Optional[Any] = None):
        full_message = f"Pipeline error"
        if stage:
            full_message += f" at {stage}"
        full_message += f": {message}"

        super().__init__(
            message=full_message,
            error_code="PIPELINE_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class DatabaseException(AppException):
    """Database operation error exception (500)."""

    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"Database error: {message}",
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class ServiceUnavailableException(AppException):
    """Service unavailable exception (503)."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# Error code constants for easier reference
class ErrorCodes:
    """Constants for all error codes used in the application."""

    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Authentication/Authorization (401, 403)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Not found (404)
    NOT_FOUND = "NOT_FOUND"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"

    # Conflict (409)
    CONFLICT = "CONFLICT"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    PROJECT_NAME_EXISTS = "PROJECT_NAME_EXISTS"

    # Pipeline errors (422)
    PIPELINE_ERROR = "PIPELINE_ERROR"
    CRAWL_FAILED = "CRAWL_FAILED"
    PREPROCESSING_FAILED = "PREPROCESSING_FAILED"
    TRANSFORM_FAILED = "TRANSFORM_FAILED"
    MODEL_TRAINING_FAILED = "MODEL_TRAINING_FAILED"

    # Database errors (500)
    DATABASE_ERROR = "DATABASE_ERROR"
    QUERY_FAILED = "QUERY_FAILED"
    CONNECTION_FAILED = "CONNECTION_FAILED"

    # Service errors (503)
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"

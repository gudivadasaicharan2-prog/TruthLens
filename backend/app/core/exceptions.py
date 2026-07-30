"""
Centralized Exception Handling
==============================
Implements consistent JSON error responses for all exceptions.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.logger import get_adapter, get_request_id


logger = get_adapter("exceptions")


class TruthLensError(Exception):
    """Base exception for TruthLens application errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(TruthLensError):
    """Validation error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class FileUploadError(TruthLensError):
    """File upload error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            status_code=400,
            details=details
        )


class AnalysisError(TruthLensError):
    """Analysis error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ANALYSIS_ERROR",
            status_code=500,
            details=details
        )


class AuthenticationError(TruthLensError):
    """Authentication error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a consistent error response.
    
    Args:
        error_code: Error code
        message: Error message
        status_code: HTTP status code
        request_id: Request ID for tracing
        details: Additional error details
        
    Returns:
        JSONResponse with error information
    """
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    if details:
        error_response["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def truth_lens_exception_handler(request: Request, exc: TruthLensError) -> JSONResponse:
    """
    Handle TruthLens application exceptions.
    
    Args:
        request: The FastAPI request
        exc: The TruthLens exception
        
    Returns:
        JSONResponse with error information
    """
    request_id = get_request_id()
    
    logger.error(
        "Application error",
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details
    )
    
    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        status_code=exc.status_code,
        request_id=request_id,
        details=exc.details
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions.
    
    Args:
        request: The FastAPI request
        exc: The HTTP exception
        
    Returns:
        JSONResponse with error information
    """
    request_id = get_request_id()
    
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail
    )
    
    error_code = f"HTTP_{exc.status_code}"
    
    return create_error_response(
        error_code=error_code,
        message=str(exc.detail),
        status_code=exc.status_code,
        request_id=request_id
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation exceptions.
    
    Args:
        request: The FastAPI request
        exc: The validation exception
        
    Returns:
        JSONResponse with error information
    """
    request_id = get_request_id()
    
    # Extract validation errors
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        "Validation error",
        errors=validation_errors
    )
    
    return create_error_response(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=422,
        request_id=request_id,
        details={"validation_errors": validation_errors}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general unhandled exceptions.
    
    Args:
        request: The FastAPI request
        exc: The unhandled exception
        
    Returns:
        JSONResponse with error information
    """
    request_id = get_request_id()
    
    logger.error(
        "Unhandled exception",
        error_type=type(exc).__name__,
        error_message=str(exc)
    )
    
    # Don't expose internal error details in production
    if request.app.state.config.ENVIRONMENT == "production":
        message = "An internal error occurred. Please try again later."
    else:
        message = f"Internal error: {str(exc)}"
    
    return create_error_response(
        error_code="INTERNAL_ERROR",
        message=message,
        status_code=500,
        request_id=request_id
    )

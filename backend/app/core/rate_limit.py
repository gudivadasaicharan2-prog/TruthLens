"""
Rate Limiting Middleware
========================
Implements API rate limiting using slowapi to protect against abuse and DoS attacks.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from app.core.config import settings
from typing import Callable


# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute", f"{settings.RATE_LIMIT_PER_HOUR}/hour"]
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> HTTPException:
    """
    Custom handler for rate limit exceeded errors.
    
    Args:
        request: The FastAPI request object
        exc: The RateLimitExceeded exception
        
    Returns:
        HTTPException with 429 status code
    """
    return HTTPException(
        status_code=429,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": str(exc.detail)
        }
    )


# Custom rate limit decorators for specific endpoints
def get_rate_limit(endpoint_type: str) -> str:
    """
    Get rate limit for specific endpoint types.
    
    Args:
        endpoint_type: Type of endpoint (image_upload, report_generation, batch_analysis, etc.)
        
    Returns:
        Rate limit string (e.g., "10/minute")
    """
    limits = {
        "image_upload": "10/minute",
        "report_generation": "20/minute",
        "batch_analysis": "5/minute",
        "compare_mode": "15/minute",
        "health": "60/minute",
        "auth": "10/minute",
        "default": f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
    }
    
    return limits.get(endpoint_type, limits["default"])


def is_rate_limiting_enabled() -> bool:
    """
    Check if rate limiting is enabled.
    
    Returns:
        True if rate limiting is enabled, False otherwise
    """
    return settings.RATE_LIMIT_ENABLED


def apply_rate_limit(endpoint_type: str = "default"):
    """
    Apply rate limiting to an endpoint.
    
    Args:
        endpoint_type: Type of endpoint for custom limits
        
    Returns:
        Decorator function or None if rate limiting is disabled
    """
    if not is_rate_limiting_enabled():
        return lambda func: func
    
    rate_limit = get_rate_limit(endpoint_type)
    return limiter.limit(rate_limit)

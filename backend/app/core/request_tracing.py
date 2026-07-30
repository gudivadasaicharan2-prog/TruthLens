"""
Request Tracing Middleware
===========================
Implements unique request ID assignment and propagation through the request pipeline.
"""

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logger import set_request_id, get_request_id


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to assign unique request IDs and propagate through the pipeline.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Set request ID in context for logging
        set_request_id(request_id)
        
        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


def get_request_id_from_request(request: Request) -> str:
    """
    Get the request ID from the request state.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The request ID
    """
    return getattr(request.state, "request_id", "unknown")

"""
Structured Logging Module
==========================
Replaces print() statements with structured JSON logging for observability.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar
from app.core.config import settings


# Context variable for request ID
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as structured JSON.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: The log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request ID if available
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


def setup_logging() -> logging.Logger:
    """
    Set up structured logging for the application.
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("truthlens")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = StructuredFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"truthlens.{name}")


def set_request_id(request_id: str) -> None:
    """
    Set the request ID in the context.
    
    Args:
        request_id: The request ID to set
    """
    request_id_ctx.set(request_id)


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.
    
    Returns:
        The request ID or None if not set
    """
    return request_id_ctx.get()


class LoggerAdapter:
    """
    Adapter for logging with additional context.
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def _log(self, level: int, message: str, **kwargs):
        """
        Internal logging method.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional fields to include in log
        """
        extra_fields = {k: v for k, v in kwargs.items() if v is not None}
        
        # Create log record with extra fields
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            None,  # fn
            None,  # lno
            message,
            None,  # args
            None,  # exc_info
        )
        record.extra_fields = extra_fields
        
        self.logger.handle(record)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)


def get_adapter(name: str) -> LoggerAdapter:
    """
    Get a logger adapter with the specified name.
    
    Args:
        name: Name of the logger
        
    Returns:
        LoggerAdapter instance
    """
    logger = get_logger(name)
    return LoggerAdapter(logger)


# Initialize logging
setup_logging()

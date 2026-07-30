"""
Performance Metrics Module
===========================
Measures and tracks performance metrics for operations.
"""

import time
from typing import Dict, Optional, Any
from contextlib import contextmanager
from app.core.logger import get_adapter


logger = get_adapter("metrics")


class PerformanceMetrics:
    """
    Tracks performance metrics for operations.
    """
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
    
    def start(self) -> None:
        """Start timing the overall request."""
        self.start_time = time.time()
        self.metrics = {
            "upload_time": None,
            "preprocessing_time": None,
            "inference_time": None,
            "gradcam_time": None,
            "pdf_generation_time": None,
            "total_time": None
        }
    
    def record_upload(self, duration: float) -> None:
        """Record upload time."""
        self.metrics["upload_time"] = duration
    
    def record_preprocessing(self, duration: float) -> None:
        """Record preprocessing time."""
        self.metrics["preprocessing_time"] = duration
    
    def record_inference(self, duration: float) -> None:
        """Record inference time."""
        self.metrics["inference_time"] = duration
    
    def record_gradcam(self, duration: float) -> None:
        """Record Grad-CAM generation time."""
        self.metrics["gradcam_time"] = duration
    
    def record_pdf_generation(self, duration: float) -> None:
        """Record PDF generation time."""
        self.metrics["pdf_generation_time"] = duration
    
    def finish(self) -> Dict[str, Any]:
        """Finish timing and return all metrics."""
        if self.start_time:
            self.metrics["total_time"] = time.time() - self.start_time
        return self.metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of recorded metrics."""
        return {
            k: v for k, v in self.metrics.items() if v is not None
        }


class MetricsContext:
    """
    Context manager for timing operations.
    """
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        self.duration: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            self.duration = time.time() - self.start_time
            logger.debug(
                f"Operation completed",
                operation=self.operation_name,
                duration_seconds=self.duration
            )
        return False  # Don't suppress exceptions


@contextmanager
def measure_operation(operation_name: str):
    """
    Context manager to measure operation duration.
    
    Args:
        operation_name: Name of the operation being measured
        
    Yields:
        MetricsContext instance
    """
    with MetricsContext(operation_name) as ctx:
        yield ctx


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get a summary of system performance metrics.
    
    Returns:
        Dictionary with performance metrics
    """
    # This could be expanded to include system-wide metrics
    # For now, returns basic information
    return {
        "metrics_enabled": True,
        "tracked_operations": [
            "upload_time",
            "preprocessing_time",
            "inference_time",
            "gradcam_time",
            "pdf_generation_time",
            "total_time"
        ]
    }

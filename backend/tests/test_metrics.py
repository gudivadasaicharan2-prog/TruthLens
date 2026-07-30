"""
Unit tests for metrics module.
"""

import pytest
import time
from app.core.metrics import (
    PerformanceMetrics,
    MetricsContext,
    measure_operation,
    get_metrics_summary
)


class TestMetrics:
    """Test suite for performance metrics."""
    
    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization."""
        metrics = PerformanceMetrics()
        assert metrics.metrics is not None
        assert "upload_time" in metrics.metrics
        assert "inference_time" in metrics.metrics
        assert "total_time" in metrics.metrics
    
    def test_performance_metrics_start(self):
        """Test starting metrics collection."""
        metrics = PerformanceMetrics()
        metrics.start()
        assert metrics.start_time is not None
    
    def test_performance_metrics_record_upload(self):
        """Test recording upload time."""
        metrics = PerformanceMetrics()
        metrics.record_upload(1.5)
        assert metrics.metrics["upload_time"] == 1.5
    
    def test_performance_metrics_record_inference(self):
        """Test recording inference time."""
        metrics = PerformanceMetrics()
        metrics.record_inference(2.5)
        assert metrics.metrics["inference_time"] == 2.5
    
    def test_performance_metrics_finish(self):
        """Test finishing metrics collection."""
        metrics = PerformanceMetrics()
        metrics.start()
        time.sleep(0.1)
        final_metrics = metrics.finish()
        assert final_metrics["total_time"] >= 0.1
    
    def test_performance_metrics_get_summary(self):
        """Test getting metrics summary."""
        metrics = PerformanceMetrics()
        metrics.record_upload(1.0)
        metrics.record_inference(2.0)
        summary = metrics.get_summary()
        assert "upload_time" in summary
        assert "inference_time" in summary
    
    def test_metrics_context(self):
        """Test MetricsContext context manager."""
        with MetricsContext("test_operation") as ctx:
            time.sleep(0.05)
        assert ctx.duration is not None
        assert ctx.duration >= 0.05
    
    def test_measure_operation(self):
        """Test measure_operation context manager."""
        with measure_operation("test_operation") as ctx:
            time.sleep(0.05)
        assert ctx.duration is not None
    
    def test_get_metrics_summary(self):
        """Test getting system metrics summary."""
        summary = get_metrics_summary()
        assert summary is not None
        assert "metrics_enabled" in summary
        assert "tracked_operations" in summary

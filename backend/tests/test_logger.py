"""
Unit tests for logging module.
"""

import pytest
import json
from app.core.logger import (
    setup_logging,
    get_adapter,
    set_request_id,
    get_request_id
)


class TestLogger:
    """Test suite for logging module."""
    
    def test_setup_logging(self):
        """Test logging setup."""
        logger = setup_logging()
        assert logger is not None
        assert logger.name == "truthlens"
    
    def test_get_adapter(self):
        """Test getting logger adapter."""
        adapter = get_adapter("test")
        assert adapter is not None
        assert adapter.logger.name == "truthlens.test"
    
    def test_set_and_get_request_id(self):
        """Test request ID context management."""
        test_id = "test-request-id-123"
        set_request_id(test_id)
        retrieved_id = get_request_id()
        assert retrieved_id == test_id
    
    def test_get_request_id_none(self):
        """Test getting request ID when not set."""
        # Clear any existing request ID
        set_request_id(None)
        retrieved_id = get_request_id()
        assert retrieved_id is None
    
    def test_adapter_info_log(self, caplog):
        """Test adapter info logging."""
        adapter = get_adapter("test")
        adapter.info("Test message", key="value")
        # Log should be captured
        assert len(caplog.records) > 0
    
    def test_adapter_error_log(self, caplog):
        """Test adapter error logging."""
        adapter = get_adapter("test")
        adapter.error("Test error", error_code="TEST_ERROR")
        # Log should be captured
        assert len(caplog.records) > 0

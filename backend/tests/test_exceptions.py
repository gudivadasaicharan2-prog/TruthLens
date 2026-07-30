"""
Unit tests for exception handling module.
"""

import pytest
from fastapi import Request
from app.core.exceptions import (
    TruthLensError,
    ValidationError,
    FileUploadError,
    AnalysisError,
    AuthenticationError,
    create_error_response
)


class TestExceptions:
    """Test suite for exception handling."""
    
    def test_truth_lens_error_creation(self):
        """Test TruthLensError creation."""
        error = TruthLensError(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=500,
            details={"key": "value"}
        )
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.status_code == 500
        assert error.details == {"key": "value"}
    
    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == 400
    
    def test_file_upload_error_creation(self):
        """Test FileUploadError creation."""
        error = FileUploadError("File too large")
        assert error.message == "File too large"
        assert error.error_code == "FILE_UPLOAD_ERROR"
        assert error.status_code == 400
    
    def test_analysis_error_creation(self):
        """Test AnalysisError creation."""
        error = AnalysisError("Analysis failed")
        assert error.message == "Analysis failed"
        assert error.error_code == "ANALYSIS_ERROR"
        assert error.status_code == 500
    
    def test_authentication_error_creation(self):
        """Test AuthenticationError creation."""
        error = AuthenticationError("Invalid credentials")
        assert error.message == "Invalid credentials"
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.status_code == 401
    
    def test_create_error_response(self):
        """Test error response creation."""
        response = create_error_response(
            error_code="TEST_ERROR",
            message="Test message",
            status_code=400,
            request_id="test-123",
            details={"field": "value"}
        )
        assert response.status_code == 400
        data = response.body.decode()
        assert "TEST_ERROR" in data
        assert "Test message" in data
        assert "test-123" in data

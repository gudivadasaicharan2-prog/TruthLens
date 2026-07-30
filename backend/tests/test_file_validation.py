"""
Unit tests for file validation module.
"""

import pytest
import os
import tempfile
from pathlib import Path
from app.core.file_validation import (
    validate_file_upload,
    validate_magic_bytes,
    validate_mime_type,
    validate_file_extension,
    validate_file_size,
    validate_safe_file
)


class TestFileValidation:
    """Test suite for file validation functions."""
    
    def test_validate_magic_bytes_jpeg(self):
        """Test JPEG magic bytes detection."""
        # JPEG magic bytes: FF D8 FF
        jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
        result = validate_magic_bytes(jpeg_header, "image/jpeg")
        assert result is True
    
    def test_validate_magic_bytes_png(self):
        """Test PNG magic bytes detection."""
        # PNG magic bytes: 89 50 4E 47 0D 0A 1A 0A
        png_header = b'\x89PNG\r\n\x1A\n'
        result = validate_magic_bytes(png_header, "image/png")
        assert result is True
    
    def test_validate_magic_bytes_invalid(self):
        """Test invalid magic bytes detection."""
        invalid_header = b'This is not an image'
        result = validate_magic_bytes(invalid_header, "image/jpeg")
        assert result is False
    
    def test_validate_mime_type_valid(self):
        """Test valid MIME type validation."""
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        result = validate_mime_type("image/jpeg", allowed_types)
        assert result is True
    
    def test_validate_mime_type_invalid(self):
        """Test invalid MIME type validation."""
        allowed_types = ["image/jpeg", "image/png"]
        result = validate_mime_type("application/pdf", allowed_types)
        assert result is False
    
    def test_validate_file_extension_valid(self):
        """Test valid file extension validation."""
        allowed_extensions = [".jpg", ".jpeg", ".png"]
        result = validate_file_extension("test.jpg", allowed_extensions)
        assert result is True
    
    def test_validate_file_extension_invalid(self):
        """Test invalid file extension validation."""
        allowed_extensions = [".jpg", ".jpeg", ".png"]
        result = validate_file_extension("test.exe", allowed_extensions)
        assert result is False
    
    def test_validate_file_size_valid(self):
        """Test valid file size validation."""
        result = validate_file_size(1024 * 1024, 10 * 1024 * 1024)  # 1MB, 10MB limit
        assert result is True
    
    def test_validate_file_size_invalid(self):
        """Test invalid file size validation."""
        result = validate_file_size(20 * 1024 * 1024, 10 * 1024 * 1024)  # 20MB, 10MB limit
        assert result is False
    
    def test_validate_safe_file_text(self):
        """Test safe file validation for text file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a text file")
            temp_path = f.name
        
        try:
            result = validate_safe_file(temp_path)
            # Text files should be rejected as not safe for image processing
            assert result is False
        finally:
            os.unlink(temp_path)
    
    def test_validate_safe_file_executable(self):
        """Test safe file validation for executable."""
        # MZ header for Windows executable
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.exe', delete=False) as f:
            f.write(b'MZ\x90\x00')
            temp_path = f.name
        
        try:
            result = validate_safe_file(temp_path)
            # Executables should be rejected
            assert result is False
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_upload_success(self):
        """Test successful file upload validation."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
            # Write JPEG header
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
            f.write(b'\x00' * 100)  # Add some content
            temp_path = f.name
        
        try:
            allowed_types = ["image/jpeg", "image/png"]
            max_size = 10 * 1024 * 1024
            is_valid, error_msg = validate_file_upload(
                filename="test.jpg",
                content_type="image/jpeg",
                file_size=200,
                file_path=temp_path,
                allowed_mime_types=allowed_types,
                max_file_size=max_size
            )
            assert is_valid is True
            assert error_msg is None
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_upload_wrong_extension(self):
        """Test file upload validation with wrong extension."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
            temp_path = f.name
        
        try:
            allowed_types = ["image/jpeg"]
            max_size = 10 * 1024 * 1024
            is_valid, error_msg = validate_file_upload(
                filename="test.exe",  # Wrong extension
                content_type="image/jpeg",
                file_size=200,
                file_path=temp_path,
                allowed_mime_types=allowed_types,
                max_file_size=max_size
            )
            assert is_valid is False
            assert "extension" in error_msg.lower()
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_upload_too_large(self):
        """Test file upload validation with file too large."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg', delete=False) as f:
            f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
            temp_path = f.name
        
        try:
            allowed_types = ["image/jpeg"]
            max_size = 1024  # 1KB limit
            is_valid, error_msg = validate_file_upload(
                filename="test.jpg",
                content_type="image/jpeg",
                file_size=10 * 1024,  # 10KB
                file_path=temp_path,
                allowed_mime_types=allowed_types,
                max_file_size=max_size
            )
            assert is_valid is False
            assert "size" in error_msg.lower()
        finally:
            os.unlink(temp_path)

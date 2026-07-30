"""
Pytest configuration and fixtures for TruthLens backend tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["SECRET_KEY"] = "test_secret_key_32_characters_long"
os.environ["JWT_SECRET"] = "test_jwt_secret_32_characters_long"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"
os.environ["RATE_LIMIT_ENABLED"] = "false"


@pytest.fixture
def sample_image_path():
    """Path to a sample test image."""
    return Path(__file__).parent / "fixtures" / "sample.jpg"


@pytest.fixture
def sample_text_file():
    """Path to a sample text file for negative testing."""
    return Path(__file__).parent / "fixtures" / "sample.txt"


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Temporary upload directory for testing."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return str(upload_dir)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from app.core.config import Settings
    return Settings()

"""
Unit tests for configuration module.
"""

import pytest
import os
from app.core.config import Settings


class TestConfiguration:
    """Test suite for configuration validation."""
    
    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings()
        assert settings.ENVIRONMENT == "development"
        assert settings.RATE_LIMIT_ENABLED is True
        assert settings.MAX_FILE_SIZE == 10485760  # 10MB
    
    def test_environment_variable_override(self):
        """Test environment variable overrides."""
        os.environ["ENVIRONMENT"] = "production"
        os.environ["RATE_LIMIT_ENABLED"] = "false"
        settings = Settings()
        assert settings.ENVIRONMENT == "production"
        assert settings.RATE_LIMIT_ENABLED is False
    
    def test_validate_required_secrets_success(self):
        """Test successful secret validation."""
        os.environ["SECRET_KEY"] = "test_secret_key_32_characters_long"
        os.environ["JWT_SECRET"] = "test_jwt_secret_32_characters_long"
        os.environ["DATABASE_URL"] = "postgresql://localhost/test"
        settings = Settings()
        # Should not raise an exception
        settings.validate_required_secrets()
    
    def test_validate_required_secrets_missing_secret_key(self):
        """Test validation fails when SECRET_KEY is missing."""
        os.environ["SECRET_KEY"] = ""
        settings = Settings()
        with pytest.raises(ValueError, match="SECRET_KEY"):
            settings.validate_required_secrets()
    
    def test_validate_required_secrets_missing_jwt_secret(self):
        """Test validation fails when JWT_SECRET is missing."""
        os.environ["SECRET_KEY"] = "test_secret_key_32_characters_long"
        os.environ["JWT_SECRET"] = ""
        settings = Settings()
        with pytest.raises(ValueError, match="JWT_SECRET"):
            settings.validate_required_secrets()
    
    def test_validate_required_secrets_too_short(self):
        """Test validation fails when secret is too short."""
        os.environ["SECRET_KEY"] = "short"
        settings = Settings()
        with pytest.raises(ValueError, match="at least 32 characters"):
            settings.validate_required_secrets()
    
    def test_validate_production_environment(self):
        """Test production environment validation."""
        os.environ["ENVIRONMENT"] = "production"
        os.environ["SECRET_KEY"] = "test_secret_key_32_characters_long"
        os.environ["JWT_SECRET"] = "test_jwt_secret_32_characters_long"
        os.environ["DATABASE_URL"] = "postgresql://localhost/test"
        settings = Settings()
        # Should not raise an exception
        settings.validate_required_secrets()
    
    def test_validate_production_with_development_secret(self):
        """Test production rejects development secrets."""
        os.environ["ENVIRONMENT"] = "production"
        os.environ["SECRET_KEY"] = "dev-secret-key-change-in-production"
        os.environ["JWT_SECRET"] = "test_jwt_secret_32_characters_long"
        os.environ["DATABASE_URL"] = "postgresql://localhost/test"
        settings = Settings()
        with pytest.raises(ValueError, match="production"):
            settings.validate_required_secrets()
    
    def test_cors_origins_parsing(self):
        """Test CORS origins parsing."""
        os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000,https://example.com"
        settings = Settings()
        assert len(settings.cors_origins) == 2
        assert "http://localhost:3000" in settings.cors_origins
        assert "https://example.com" in settings.cors_origins
    
    def test_cors_origins_empty(self):
        """Test CORS origins when empty."""
        os.environ["ALLOWED_ORIGINS"] = ""
        settings = Settings()
        assert settings.cors_origins == []
    
    def test_allowed_mime_types_parsing(self):
        """Test allowed MIME types parsing."""
        os.environ["ALLOWED_MIME_TYPES"] = "image/jpeg,image/png,image/webp"
        settings = Settings()
        assert len(settings.allowed_mime_types) == 3
        assert "image/jpeg" in settings.allowed_mime_types
        assert "image/png" in settings.allowed_mime_types

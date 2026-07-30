from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import secrets


class Settings(BaseSettings):
    # Database Configuration - REQUIRED
    DATABASE_URL: str = ""
    
    # Security Configuration - REQUIRED
    SECRET_KEY: str = ""
    JWT_SECRET: str = ""
    
    # Token Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # File Upload Configuration
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB in bytes
    ALLOWED_MIME_TYPES: str = "image/jpeg,image/jpg,image/png,image/webp,image/gif,image/bmp"
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = ""
    
    # External API Keys (Optional)
    GOOGLE_CLIENT_ID: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    GNEWS_API_KEY: Optional[str] = None
    HF_TOKEN: Optional[str] = None
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 30
    RATE_LIMIT_PER_HOUR: int = 200
    
    # Security Headers Configuration
    ENABLE_HSTS: bool = False  # Enable in production with HTTPS
    HSTS_MAX_AGE: int = 31536000  # 1 year
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    
    @property
    def cors_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return []
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def allowed_mime_types(self) -> List[str]:
        if not self.ALLOWED_MIME_TYPES:
            return ["image/jpeg", "image/png", "image/webp"]
        return [mime.strip() for mime in self.ALLOWED_MIME_TYPES.split(",")]

    def validate_required_secrets(self) -> None:
        """Validate that required secrets are set."""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is required")
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY environment variable must be at least 32 characters")
        if not self.JWT_SECRET or len(self.JWT_SECRET) < 32:
            raise ValueError("JWT_SECRET environment variable must be at least 32 characters")
        
        # Warn if using development secrets in production
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY in ["supersecretjwtkey123", "dev-secret-key"]:
                raise ValueError("Cannot use development SECRET_KEY in production")
            if self.JWT_SECRET in ["supersecretjwtkey123", "dev-secret-key"]:
                raise ValueError("Cannot use development JWT_SECRET in production")

    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get and validate settings."""
    settings = Settings()
    settings.validate_required_secrets()
    return settings


settings = get_settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

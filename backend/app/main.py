from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import os
import sys
import signal
import time
import torch
from app.core.config import settings
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.health import router as health_router
from app.core.logger import setup_logging, get_adapter
from app.core.request_tracing import RequestTracingMiddleware
from app.core.exceptions import (
    truth_lens_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    TruthLensError
)
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Force UTF-8 on Windows consoles (prevents charmap/cp1252 UnicodeEncodeError
# when print() outputs non-ASCII characters during request handling)
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass  # Python < 3.7 or non-reconfigurable stream

# Setup structured logging
setup_logging()
logger = get_adapter("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm-load ML models once at startup to avoid first-request latency."""
    logger.info("Application startup initiated", environment=settings.ENVIRONMENT)
    
    # Validate configuration at startup
    logger.info("Validating configuration")
    try:
        settings.validate_required_secrets()
        logger.info("Configuration validation passed")
    except ValueError as e:
        logger.error("Configuration validation failed", error=str(e))
        raise
    
    # Log configuration summary (without secrets)
    logger.info("Configuration summary",
                environment=settings.ENVIRONMENT,
                rate_limiting_enabled=settings.RATE_LIMIT_ENABLED,
                max_file_size_mb=round(settings.MAX_FILE_SIZE / (1024 * 1024), 2),
                cors_origins_count=len(settings.cors_origins))
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received", signal=signum)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check upload directory
    logger.info("Checking upload directories")
    for d in ["./uploads/images", "./uploads/videos", "./uploads/frames"]:
        os.makedirs(d, exist_ok=True)
        if not os.access(d, os.W_OK):
            logger.error("Upload directory not writable", directory=d)
            raise PermissionError(f"Upload directory not writable: {d}")
    logger.info("Upload directories verified")
    
    # Check database connection
    logger.info("Checking database connection")
    try:
        from app.core.database import engine
        from sqlalchemy import text
        if engine is not None:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection verified")
        else:
            logger.warning("Database engine not initialized")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise
    
    # Load ML models
    logger.info("Loading ML models")
    try:
        from app.ai.models.image_model import load_model, is_using_trained_weights
        load_model()
        logger.info("ML models loaded successfully", 
                   model="EfficientNet-B2",
                   using_trained_weights=is_using_trained_weights())
    except Exception as e:
        logger.warning("ML model load warning", error=str(e))
    
    # Check GPU availability
    logger.info("Checking GPU availability")
    try:
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            logger.info("GPU available", 
                       device_count=gpu_count,
                       device_name=torch.cuda.get_device_name(0) if gpu_count > 0 else None)
        else:
            logger.info("GPU not available, using CPU")
    except Exception as e:
        logger.warning("GPU check failed", error=str(e))
    
    logger.info("Application ready to accept requests")
    yield
    
    # Graceful shutdown
    logger.info("Application shutdown initiated")
    
    # Clean up GPU memory
    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
            logger.info("GPU memory cleared")
        except Exception as e:
            logger.error("Error clearing GPU memory", error=str(e))
    
    # Clean up temporary files
    try:
        import shutil
        temp_dirs = ["./uploads/images", "./uploads/videos", "./uploads/frames"]
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                # Clean up files older than 1 hour
                current_time = time.time()
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_mtime = os.path.getmtime(file_path)
                            if current_time - file_mtime > 3600:  # 1 hour
                                os.remove(file_path)
                                logger.debug("Removed temporary file", path=file_path)
                        except Exception as e:
                            logger.warning("Failed to remove temporary file", path=file_path, error=str(e))
        logger.info("Temporary files cleaned up")
    except Exception as e:
        logger.error("Error cleaning up temporary files", error=str(e))
    
    # Close database connections
    try:
        from app.core.database import engine
        if engine is not None:
            engine.dispose()
            logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error closing database connections", error=str(e))
    
    logger.info("Application shutdown complete")


app = FastAPI(
    title="TruthLens API",
    version="2.1.0",
    description="AI Image & Video Authenticity Platform",
    lifespan=lifespan,
)

# Store config in app state for exception handlers
app.state.config = settings

# Rate limiting error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Exception handlers
app.add_exception_handler(TruthLensError, truth_lens_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Request tracing middleware (must be first)
app.add_middleware(RequestTracingMiddleware)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS - Environment-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload dirs
# Note: This is now done in lifespan for validation

# Register health check router
app.include_router(health_router, prefix="/health", tags=["Health"])

# Legacy health endpoint for backward compatibility
@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "TruthLens API v2 running",
        "version": "2.1.0",
        "platform": "AI Image & Video Authenticity"
    }

# Register routers safely
def register(module_path, prefix, tag):
    try:
        import importlib
        module = importlib.import_module(module_path)
        app.include_router(module.router, prefix=prefix, tags=[tag])
        logger.info("Router registered", tag=tag, prefix=prefix)
    except Exception as e:
        logger.error("Router registration failed", tag=tag, error=str(e))

register("app.api.v1.auth",      "/api/v1/auth",      "Auth")
register("app.api.v1.image",     "/api/v1/image",     "Image")
register("app.api.v1.video",     "/api/v1/video",     "Video")
register("app.api.v1.users",     "/api/v1/users",     "Users")
# NOTE: news and factcheck routes removed — platform is now media-only (ASCII safe comment)

"""
Health Check Module
===================
Implements comprehensive health check endpoints for monitoring service status.
"""

import os
import shutil
import torch
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.core.resource_monitor import (
    get_cpu_usage,
    get_memory_usage,
    get_gpu_usage,
    get_disk_usage,
    check_resource_thresholds
)

router = APIRouter()


def get_disk_space(path: str = ".") -> Dict[str, int]:
    """
    Get disk space information.
    
    Args:
        path: Path to check disk space for
        
    Returns:
        Dictionary with total, used, and free space in bytes
    """
    try:
        total, used, free = shutil.disk_usage(path)
        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "used_percent": round((used / total) * 100, 2),
            "free_percent": round((free / total) * 100, 2)
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_bytes": 0,
            "used_bytes": 0,
            "free_bytes": 0,
            "used_percent": 0,
            "free_percent": 0
        }


def get_memory_info() -> Dict[str, Any]:
    """
    Get memory information.
    
    Returns:
        Dictionary with memory usage information
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        return {
            "rss_bytes": mem_info.rss,
            "vms_bytes": mem_info.vms,
            "rss_mb": round(mem_info.rss / (1024 * 1024), 2),
            "vms_mb": round(mem_info.vms / (1024 * 1024), 2),
            "percent": round(process.memory_percent(), 2)
        }
    except ImportError:
        # Fallback if psutil not available
        return {
            "rss_bytes": 0,
            "vms_bytes": 0,
            "rss_mb": 0,
            "vms_mb": 0,
            "percent": 0,
            "note": "psutil not installed"
        }
    except Exception as e:
        return {
            "error": str(e),
            "rss_bytes": 0,
            "vms_bytes": 0,
            "rss_mb": 0,
            "vms_mb": 0,
            "percent": 0
        }


def get_gpu_info() -> Dict[str, Any]:
    """
    Get GPU information.
    
    Returns:
        Dictionary with GPU availability and information
    """
    try:
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_info = {
                "available": True,
                "device_count": gpu_count,
                "current_device": torch.cuda.current_device(),
                "device_name": torch.cuda.get_device_name(0) if gpu_count > 0 else None,
                "memory_allocated": round(torch.cuda.memory_allocated(0) / (1024 ** 3), 2),
                "memory_reserved": round(torch.cuda.memory_reserved(0) / (1024 ** 3), 2),
                "memory_total": round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2) if gpu_count > 0 else 0
            }
            return gpu_info
        else:
            return {
                "available": False,
                "device_count": 0,
                "note": "CUDA not available, using CPU"
            }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


def get_model_status() -> Dict[str, Any]:
    """
    Get ML model loading status.
    
    Returns:
        Dictionary with model status information
    """
    try:
        from app.ai.models.image_model import is_using_trained_weights, _BACKBONE, _CLASSIFIER
        
        return {
            "backbone_loaded": _BACKBONE is not None,
            "classifier_loaded": _CLASSIFIER is not None,
            "using_trained_weights": is_using_trained_weights(),
            "model_type": "EfficientNet-B2"
        }
    except Exception as e:
        return {
            "backbone_loaded": False,
            "classifier_loaded": False,
            "using_trained_weights": False,
            "error": str(e)
        }


def get_database_status() -> Dict[str, Any]:
    """
    Get database connection status.
    
    Returns:
        Dictionary with database status information
    """
    try:
        if engine is None:
            return {
                "connected": False,
                "error": "Database engine not initialized"
            }
        
        # Try to execute a simple query
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "connected": True,
            "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "unknown"
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e)
        }


def get_upload_dir_status() -> Dict[str, Any]:
    """
    Get upload directory status.
    
    Returns:
        Dictionary with upload directory information
    """
    try:
        upload_dir = settings.UPLOAD_DIR
        if not os.path.exists(upload_dir):
            return {
                "exists": False,
                "path": upload_dir,
                "error": "Upload directory does not exist"
            }
        
        # Count files in upload directory
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(upload_dir):
            file_count += len(files)
            total_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
        
        return {
            "exists": True,
            "path": upload_dir,
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "writable": os.access(upload_dir, os.W_OK)
        }
    except Exception as e:
        return {
            "exists": False,
            "error": str(e)
        }


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns 200 if service is running.
    """
    return {
        "status": "healthy",
        "service": "TruthLens API",
        "version": "2.1.0",
        "environment": settings.ENVIRONMENT
    }


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    Returns 200 if service is ready to accept requests.
    Checks: Model loaded, Database connected, Upload directory writable.
    """
    checks = {
        "model": get_model_status(),
        "database": get_database_status(),
        "upload_dir": get_upload_dir_status()
    }
    
    # Determine overall readiness
    ready = (
        checks["model"].get("backbone_loaded", False) and
        checks["database"].get("connected", False) and
        checks["upload_dir"].get("writable", False)
    )
    
    status_code = 200 if ready else 503
    
    return {
        "status": "ready" if ready else "not_ready",
        "checks": checks
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check endpoint.
    Returns 200 if service is alive.
    Checks: Process running, Memory not exhausted.
    """
    memory_info = get_memory_usage()
    
    # Check if memory usage is critical (>90%)
    memory_critical = memory_info.get("percent", 0) > 90
    
    alive = not memory_critical
    
    status_code = 200 if alive else 503
    
    return {
        "status": "alive" if alive else "unhealthy",
        "memory": memory_info,
        "memory_critical": memory_critical
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check endpoint.
    Returns comprehensive health information for monitoring.
    """
    # Check resource thresholds
    thresholds = {
        "cpu_percent": 90,
        "memory_percent": 90,
        "disk_percent": 90
    }
    threshold_check = check_resource_thresholds(thresholds)
    
    return {
        "status": "healthy" if threshold_check["healthy"] else "degraded",
        "service": "TruthLens API",
        "version": "2.1.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": None,  # Will be set by response
        "checks": {
            "model": get_model_status(),
            "gpu": get_gpu_usage(),
            "database": get_database_status(),
            "memory": get_memory_usage(),
            "cpu": get_cpu_usage(),
            "disk": get_disk_usage(settings.UPLOAD_DIR),
            "upload_dir": get_upload_dir_status()
        },
        "thresholds": threshold_check,
        "configuration": {
            "rate_limiting_enabled": settings.RATE_LIMIT_ENABLED,
            "rate_limit_per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "rate_limit_per_hour": settings.RATE_LIMIT_PER_HOUR,
            "max_file_size_mb": round(settings.MAX_FILE_SIZE / (1024 * 1024), 2),
            "allowed_mime_types": settings.allowed_mime_types
        }
    }

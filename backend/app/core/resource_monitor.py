"""
Resource Monitoring Module
==========================
Monitors CPU, GPU, memory, and disk usage.
"""

import os
import shutil
import torch
from typing import Dict, Any, Optional
from app.core.logger import get_adapter


logger = get_adapter("resource_monitor")


def get_cpu_usage() -> Dict[str, Any]:
    """
    Get CPU usage information.
    
    Returns:
        Dictionary with CPU usage metrics
    """
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        return {
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count,
            "cpu_freq_mhz": cpu_freq.current if cpu_freq else None,
            "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    except ImportError:
        logger.warning("psutil not installed, CPU monitoring unavailable")
        return {
            "cpu_percent": None,
            "cpu_count": None,
            "cpu_freq_mhz": None,
            "load_avg": None,
            "note": "psutil not installed"
        }
    except Exception as e:
        logger.error("Error getting CPU usage", error=str(e))
        return {
            "cpu_percent": None,
            "cpu_count": None,
            "cpu_freq_mhz": None,
            "load_avg": None,
            "error": str(e)
        }


def get_memory_usage() -> Dict[str, Any]:
    """
    Get memory usage information.
    
    Returns:
        Dictionary with memory usage metrics
    """
    try:
        import psutil
        mem = psutil.virtual_memory()
        
        return {
            "total_bytes": mem.total,
            "available_bytes": mem.available,
            "used_bytes": mem.used,
            "free_bytes": mem.free,
            "percent": mem.percent,
            "total_mb": round(mem.total / (1024 ** 2), 2),
            "available_mb": round(mem.available / (1024 ** 2), 2),
            "used_mb": round(mem.used / (1024 ** 2), 2)
        }
    except ImportError:
        logger.warning("psutil not installed, memory monitoring unavailable")
        return {
            "total_bytes": None,
            "available_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "percent": None,
            "note": "psutil not installed"
        }
    except Exception as e:
        logger.error("Error getting memory usage", error=str(e))
        return {
            "total_bytes": None,
            "available_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "percent": None,
            "error": str(e)
        }


def get_gpu_usage() -> Dict[str, Any]:
    """
    Get GPU usage information.
    
    Returns:
        Dictionary with GPU usage metrics
    """
    try:
        if not torch.cuda.is_available():
            return {
                "available": False,
                "device_count": 0,
                "note": "CUDA not available"
            }
        
        gpu_count = torch.cuda.device_count()
        gpu_info = {
            "available": True,
            "device_count": gpu_count,
            "devices": []
        }
        
        for i in range(gpu_count):
            device_props = torch.cuda.get_device_properties(i)
            memory_allocated = torch.cuda.memory_allocated(i)
            memory_reserved = torch.cuda.memory_reserved(i)
            memory_total = device_props.total_memory
            
            gpu_info["devices"].append({
                "device_id": i,
                "name": device_props.name,
                "memory_total_bytes": memory_total,
                "memory_total_gb": round(memory_total / (1024 ** 3), 2),
                "memory_allocated_bytes": memory_allocated,
                "memory_allocated_gb": round(memory_allocated / (1024 ** 3), 2),
                "memory_reserved_bytes": memory_reserved,
                "memory_reserved_gb": round(memory_reserved / (1024 ** 3), 2),
                "memory_utilization": round((memory_allocated / memory_total) * 100, 2) if memory_total > 0 else 0
            })
        
        return gpu_info
    except Exception as e:
        logger.error("Error getting GPU usage", error=str(e))
        return {
            "available": False,
            "error": str(e)
        }


def get_disk_usage(path: str = ".") -> Dict[str, Any]:
    """
    Get disk usage information.
    
    Args:
        path: Path to check disk space for
        
    Returns:
        Dictionary with disk usage metrics
    """
    try:
        total, used, free = shutil.disk_usage(path)
        
        return {
            "path": path,
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "percent": round((used / total) * 100, 2),
            "total_gb": round(total / (1024 ** 3), 2),
            "used_gb": round(used / (1024 ** 3), 2),
            "free_gb": round(free / (1024 ** 3), 2)
        }
    except Exception as e:
        logger.error("Error getting disk usage", error=str(e))
        return {
            "path": path,
            "total_bytes": None,
            "used_bytes": None,
            "free_bytes": None,
            "percent": None,
            "error": str(e)
        }


def get_active_requests() -> Dict[str, Any]:
    """
    Get information about active requests.
    
    Returns:
        Dictionary with active request metrics
    """
    # This is a placeholder - in a real implementation, this would
    # track actual active requests from a request pool or queue
    return {
        "active_count": 0,
        "queued_count": 0,
        "note": "Request tracking not implemented"
    }


def get_resource_summary() -> Dict[str, Any]:
    """
    Get a summary of all resource usage.
    
    Returns:
        Dictionary with all resource metrics
    """
    return {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "gpu": get_gpu_usage(),
        "disk": get_disk_usage("."),
        "requests": get_active_requests(),
        "timestamp": None  # Will be set by caller
    }


def check_resource_thresholds(thresholds: Dict[str, float]) -> Dict[str, Any]:
    """
    Check if resource usage exceeds thresholds.
    
    Args:
        thresholds: Dictionary of thresholds (e.g., {"cpu_percent": 80, "memory_percent": 90})
        
    Returns:
        Dictionary with threshold violations
    """
    violations = []
    
    cpu = get_cpu_usage()
    if cpu.get("cpu_percent") and thresholds.get("cpu_percent"):
        if cpu["cpu_percent"] > thresholds["cpu_percent"]:
            violations.append({
                "resource": "cpu",
                "current": cpu["cpu_percent"],
                "threshold": thresholds["cpu_percent"]
            })
    
    memory = get_memory_usage()
    if memory.get("percent") and thresholds.get("memory_percent"):
        if memory["percent"] > thresholds["memory_percent"]:
            violations.append({
                "resource": "memory",
                "current": memory["percent"],
                "threshold": thresholds["memory_percent"]
            })
    
    disk = get_disk_usage(".")
    if disk.get("percent") and thresholds.get("disk_percent"):
        if disk["percent"] > thresholds["disk_percent"]:
            violations.append({
                "resource": "disk",
                "current": disk["percent"],
                "threshold": thresholds["disk_percent"]
            })
    
    return {
        "violations": violations,
        "healthy": len(violations) == 0
    }

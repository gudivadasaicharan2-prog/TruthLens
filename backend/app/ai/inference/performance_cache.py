"""
Performance Cache - TruthLens v2.3

Lightweight caching mechanism for expensive computations.
Caches preprocessed tensors, feature vectors, and model outputs
to avoid duplicate computations and improve inference speed.

Key features:
- LRU cache for preprocessed images
- Feature vector caching
- Model output caching
- Memory-efficient caching with size limits
"""

import hashlib
import numpy as np
from typing import Optional, Dict, Any
from functools import lru_cache


class PerformanceCache:
    """
    Performance cache for expensive computations.
    
    Uses LRU caching with memory limits to cache:
    - Preprocessed image tensors
    - Feature vectors
    - Model outputs
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize performance cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.max_size = max_size
        self._preprocess_cache: Dict[str, Any] = {}
        self._feature_cache: Dict[str, np.ndarray] = {}
        self._output_cache: Dict[str, Any] = {}
    
    def _generate_key(self, data: np.ndarray, prefix: str = "") -> str:
        """
        Generate a cache key from image data.
        
        Args:
            data: Image data as numpy array
            prefix: Prefix for the key
            
        Returns:
            Cache key string
        """
        # Use hash of image data for key
        data_bytes = data.tobytes()
        hash_obj = hashlib.md5(data_bytes)
        return f"{prefix}_{hash_obj.hexdigest()}"
    
    def get_preprocessed(self, image: np.ndarray) -> Optional[Any]:
        """
        Get cached preprocessed tensor.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Cached preprocessed tensor or None
        """
        key = self._generate_key(image, "preprocess")
        return self._preprocess_cache.get(key)
    
    def set_preprocessed(self, image: np.ndarray, tensor: Any) -> None:
        """
        Cache preprocessed tensor.
        
        Args:
            image: Input image as numpy array
            tensor: Preprocessed tensor to cache
        """
        key = self._generate_key(image, "preprocess")
        
        # LRU eviction if cache is full
        if len(self._preprocess_cache) >= self.max_size:
            # Remove oldest item (first key)
            oldest_key = next(iter(self._preprocess_cache))
            del self._preprocess_cache[oldest_key]
        
        self._preprocess_cache[key] = tensor
    
    def get_features(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Get cached feature vector.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Cached feature vector or None
        """
        key = self._generate_key(image, "features")
        return self._feature_cache.get(key)
    
    def set_features(self, image: np.ndarray, features: np.ndarray) -> None:
        """
        Cache feature vector.
        
        Args:
            image: Input image as numpy array
            features: Feature vector to cache
        """
        key = self._generate_key(image, "features")
        
        # LRU eviction if cache is full
        if len(self._feature_cache) >= self.max_size:
            oldest_key = next(iter(self._feature_cache))
            del self._feature_cache[oldest_key]
        
        self._feature_cache[key] = features.copy()
    
    def get_output(self, image: np.ndarray, model_name: str) -> Optional[Any]:
        """
        Get cached model output.
        
        Args:
            image: Input image as numpy array
            model_name: Name of the model
            
        Returns:
            Cached model output or None
        """
        key = self._generate_key(image, f"output_{model_name}")
        return self._output_cache.get(key)
    
    def set_output(self, image: np.ndarray, model_name: str, output: Any) -> None:
        """
        Cache model output.
        
        Args:
            image: Input image as numpy array
            model_name: Name of the model
            output: Model output to cache
        """
        key = self._generate_key(image, f"output_{model_name}")
        
        # LRU eviction if cache is full
        if len(self._output_cache) >= self.max_size:
            oldest_key = next(iter(self._output_cache))
            del self._output_cache[oldest_key]
        
        self._output_cache[key] = output
    
    def clear(self) -> None:
        """Clear all caches."""
        self._preprocess_cache.clear()
        self._feature_cache.clear()
        self._output_cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache sizes
        """
        return {
            "preprocess_cache_size": len(self._preprocess_cache),
            "feature_cache_size": len(self._feature_cache),
            "output_cache_size": len(self._output_cache)
        }


# Global cache instance
_global_cache: Optional[PerformanceCache] = None


def get_global_cache() -> PerformanceCache:
    """
    Get or create the global cache instance.
    
    Returns:
        Global PerformanceCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = PerformanceCache(max_size=100)
    return _global_cache


def clear_global_cache() -> None:
    """Clear the global cache."""
    global _global_cache
    if _global_cache is not None:
        _global_cache.clear()


# Decorator for caching function results
def cached_result(cache_key_prefix: str = "result"):
    """
    Decorator for caching function results.
    
    Args:
        cache_key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from arguments
            key_parts = [cache_key_prefix]
            
            # Add first numpy array argument to key
            for arg in args:
                if isinstance(arg, np.ndarray):
                    key_parts.append(arg.tobytes()[:1000])  # First 1000 bytes
                    break
            
            key_str = "_".join(key_parts)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            
            cache = get_global_cache()
            cached = cache.get_output(args[0] if args else np.array([]), key_hash)
            
            if cached is not None:
                return cached
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Cache result
            if args and isinstance(args[0], np.ndarray):
                cache.set_output(args[0], key_hash, result)
            
            return result
        
        return wrapper
    return decorator

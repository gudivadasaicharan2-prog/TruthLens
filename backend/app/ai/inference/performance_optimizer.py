"""
Performance Optimization Module for TruthLens v2.2

This module provides performance optimizations for AI detection inference,
including GPU batch processing, tensor caching, and memory management.

Key features:
- GPU batch inference optimization
- Tensor caching for reusable computations
- Memory-efficient preprocessing
- Parallel processing where appropriate
- Inference time monitoring
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
import time


class PerformanceOptimizer:
    """
    Performance optimizer for AI detection inference.
    
    Optimizes inference speed through GPU batch processing,
    tensor caching, and memory management.
    """
    
    def __init__(self, max_cache_size: int = 100):
        """
        Initialize performance optimizer.
        
        Args:
            max_cache_size: Maximum number of cached tensors
        """
        self.max_cache_size = max_cache_size
        self.tensor_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.inference_times = []
    
    def clear_cache(self):
        """Clear the tensor cache."""
        self.tensor_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'cache_size': len(self.tensor_cache),
            'max_cache_size': self.max_cache_size,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate
        }
    
    def cache_tensor(self, key: str, tensor: torch.Tensor):
        """
        Cache a tensor for reuse.
        
        Args:
            key: Cache key
            tensor: Tensor to cache
        """
        if len(self.tensor_cache) >= self.max_cache_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.tensor_cache))
            del self.tensor_cache[oldest_key]
        
        self.tensor_cache[key] = tensor.detach().clone()
    
    def get_cached_tensor(self, key: str) -> Optional[torch.Tensor]:
        """
        Get a cached tensor.
        
        Args:
            key: Cache key
            
        Returns:
            Cached tensor or None if not found
        """
        if key in self.tensor_cache:
            self.cache_hits += 1
            return self.tensor_cache[key].clone()
        else:
            self.cache_misses += 1
            return None
    
    def optimize_batch_size(
        self,
        num_items: int,
        max_batch_size: int = 32,
        min_batch_size: int = 1
    ) -> int:
        """
        Determine optimal batch size for GPU inference.
        
        Args:
            num_items: Number of items to process
            max_batch_size: Maximum batch size
            min_batch_size: Minimum batch size
            
        Returns:
            Optimal batch size
        """
        # Use power of 2 for better GPU utilization
        batch_size = min(max_batch_size, num_items)
        
        # Round down to nearest power of 2
        batch_size = 2 ** (batch_size.bit_length() - 1)
        
        return max(min_batch_size, batch_size)
    
    def batch_inference(
        self,
        model: nn.Module,
        inputs: List[torch.Tensor],
        device: str,
        batch_size: Optional[int] = None
    ) -> List[torch.Tensor]:
        """
        Perform batch inference with optimal batch size.
        
        Args:
            model: PyTorch model
            inputs: List of input tensors
            device: Device to run inference on
            batch_size: Optional batch size (auto-determined if None)
            
        Returns:
            List of output tensors
        """
        if not inputs:
            return []
        
        # Determine optimal batch size
        if batch_size is None:
            batch_size = self.optimize_batch_size(len(inputs))
        
        # Process in batches
        outputs = []
        model.eval()
        
        with torch.no_grad():
            for i in range(0, len(inputs), batch_size):
                batch = inputs[i:i + batch_size]
                batch_tensor = torch.cat(batch, dim=0).to(device)
                
                # Inference
                batch_output = model(batch_tensor)
                
                # Split batch output
                if len(batch_output.shape) > 0:
                    outputs.extend(batch_output.split(1, dim=0))
                else:
                    outputs.extend([batch_output] * len(batch))
        
        return outputs
    
    def measure_inference_time(self, func, *args, **kwargs):
        """
        Measure inference time for a function.
        
        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            (result, inference_time)
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        inference_time = end_time - start_time
        self.inference_times.append(inference_time)
        
        # Keep only last 100 measurements
        if len(self.inference_times) > 100:
            self.inference_times.pop(0)
        
        return result, inference_time
    
    def get_inference_stats(self) -> Dict:
        """
        Get inference time statistics.
        
        Returns:
            Dictionary containing inference statistics
        """
        if not self.inference_times:
            return {
                'mean_time': 0.0,
                'median_time': 0.0,
                'min_time': 0.0,
                'max_time': 0.0,
                'std_time': 0.0,
                'num_measurements': 0
            }
        
        return {
            'mean_time': float(np.mean(self.inference_times)),
            'median_time': float(np.median(self.inference_times)),
            'min_time': float(np.min(self.inference_times)),
            'max_time': float(np.max(self.inference_times)),
            'std_time': float(np.std(self.inference_times)),
            'num_measurements': len(self.inference_times)
        }
    
    def optimize_memory(self):
        """
        Optimize memory usage by clearing cache and garbage collection.
        """
        import gc
        
        # Clear tensor cache
        self.clear_cache()
        
        # Force garbage collection
        gc.collect()
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class PreprocessingCache:
    """
    Cache for preprocessing operations to avoid redundant computations.
    """
    
    def __init__(self, max_size: int = 50):
        """
        Initialize preprocessing cache.
        
        Args:
            max_size: Maximum cache size
        """
        self.max_size = max_size
        self.cache = {}
    
    def _generate_key(self, image_hash: str, operation: str) -> str:
        """Generate cache key."""
        return f"{image_hash}_{operation}"
    
    def get(self, image_hash: str, operation: str) -> Optional[np.ndarray]:
        """
        Get cached preprocessing result.
        
        Args:
            image_hash: Hash of image
            operation: Operation name
            
        Returns:
            Cached result or None
        """
        key = self._generate_key(image_hash, operation)
        return self.cache.get(key)
    
    def set(self, image_hash: str, operation: str, result: np.ndarray):
        """
        Cache preprocessing result.
        
        Args:
            image_hash: Hash of image
            operation: Operation name
            result: Result to cache
        """
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        key = self._generate_key(image_hash, operation)
        self.cache[key] = result.copy()
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()


# Global optimizer instance
_optimizer = None
_preprocessing_cache = None


def get_optimizer() -> PerformanceOptimizer:
    """
    Get or create the global performance optimizer instance.
    
    Returns:
        PerformanceOptimizer instance
    """
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer


def get_preprocessing_cache() -> PreprocessingCache:
    """
    Get or create the global preprocessing cache instance.
    
    Returns:
        PreprocessingCache instance
    """
    global _preprocessing_cache
    if _preprocessing_cache is None:
        _preprocessing_cache = PreprocessingCache()
    return _preprocessing_cache


def optimize_gpu_memory():
    """
    Optimize GPU memory usage.
    """
    optimizer = get_optimizer()
    optimizer.optimize_memory()


def get_performance_stats() -> Dict:
    """
    Get comprehensive performance statistics.
    
    Returns:
        Dictionary containing performance statistics
    """
    optimizer = get_optimizer()
    
    return {
        'cache_stats': optimizer.get_cache_stats(),
        'inference_stats': optimizer.get_inference_stats(),
        'gpu_available': torch.cuda.is_available(),
        'gpu_memory_used': torch.cuda.memory_allocated() / (1024**3) if torch.cuda.is_available() else 0.0,
        'gpu_memory_cached': torch.cuda.memory_reserved() / (1024**3) if torch.cuda.is_available() else 0.0
    }

"""
Memory and GPU leak detection tests.
"""

import pytest
import gc
import torch
import psutil
import os
from pathlib import Path


class TestMemoryLeaks:
    """Test suite for memory and GPU leak detection."""
    
    def test_python_memory_cleanup(self):
        """Test Python memory is cleaned up after operations."""
        import sys
        
        # Get initial memory
        process = psutil.Process(os.getpid())
        initial_mem = process.memory_info().rss
        
        # Create and destroy large objects
        large_list = [i for i in range(1000000)]
        large_dict = {i: i * 2 for i in range(100000)}
        
        # Delete objects
        del large_list
        del large_dict
        gc.collect()
        
        # Check memory is cleaned up
        final_mem = process.memory_info().rss
        # Memory should not have grown significantly
        mem_growth = (final_mem - initial_mem) / 1024 / 1024  # MB
        assert mem_growth < 50, f"Memory grew by {mem_growth} MB after cleanup"
    
    def test_temporary_file_cleanup(self):
        """Test temporary files are cleaned up."""
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "test.txt"
        temp_file.write_text("test content")
        
        # Verify file exists
        assert temp_file.exists()
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        # Verify directory is removed
        assert not temp_dir.exists()
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_gpu_memory_cleanup(self):
        """Test GPU memory is cleaned up."""
        # Get initial GPU memory
        initial_allocated = torch.cuda.memory_allocated(0)
        
        # Allocate GPU memory
        tensor = torch.randn(1000, 1000, device='cuda')
        
        # Verify allocation
        allocated_after = torch.cuda.memory_allocated(0)
        assert allocated_after > initial_allocated
        
        # Delete tensor and clear cache
        del tensor
        torch.cuda.empty_cache()
        
        # Verify cleanup
        final_allocated = torch.cuda.memory_allocated(0)
        # Memory should be close to initial (may not be exactly due to fragmentation)
        mem_growth = (final_allocated - initial_allocated) / 1024 / 1024  # MB
        assert mem_growth < 10, f"GPU memory grew by {mem_growth} MB after cleanup"
    
    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_gpu_memory_leak_in_loop(self):
        """Test for GPU memory leaks in repeated operations."""
        initial_allocated = torch.cuda.memory_allocated(0)
        
        # Run multiple iterations
        for _ in range(10):
            tensor = torch.randn(100, 100, device='cuda')
            result = tensor @ tensor.T
            del tensor
            del result
            torch.cuda.empty_cache()
        
        final_allocated = torch.cuda.memory_allocated(0)
        mem_growth = (final_allocated - initial_allocated) / 1024 / 1024  # MB
        assert mem_growth < 5, f"GPU memory leak detected: {mem_growth} MB growth"
    
    def test_file_handle_cleanup(self):
        """Test file handles are properly closed."""
        import tempfile
        
        # Get initial open file handles
        process = psutil.Process(os.getpid())
        initial_handles = len(process.open_files())
        
        # Open and close files
        for _ in range(10):
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
                f.write("test")
        
        # Check handles are cleaned up
        final_handles = len(process.open_files())
        handle_growth = final_handles - initial_handles
        assert handle_growth < 5, f"File handle leak detected: {handle_growth} handles still open"

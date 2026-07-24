"""
Benchmarking Module
===================
Benchmark training time, inference speed, GPU memory usage, and model size.
"""

import time
import torch
import torch.nn as nn
from pathlib import Path
from typing import Dict, Any
import json
import psutil
import os


class Benchmark:
    """
    Benchmark model performance metrics.
    
    Measures:
    - Training time per epoch
    - Inference speed (samples/second)
    - GPU memory usage
    - Model size (disk)
    - Model parameters
    """
    
    def __init__(self, model: nn.Module, device: torch.device):
        """
        Initialize benchmark.
        
        Args:
            model: Model to benchmark
            device: Device to benchmark on
        """
        self.model = model
        self.device = device
        self.results = {
            'model_info': {},
            'training': {},
            'inference': {},
            'memory': {},
            'size': {}
        }
    
    def measure_model_info(self) -> Dict[str, Any]:
        """
        Measure model information.
        
        Returns:
            Model information dictionary
        """
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        info = {
            'total_parameters': int(total_params),
            'trainable_parameters': int(trainable_params),
            'non_trainable_parameters': int(total_params - trainable_params)
        }
        
        self.results['model_info'] = info
        return info
    
    def measure_model_size(self, checkpoint_path: str) -> Dict[str, Any]:
        """
        Measure model size on disk.
        
        Args:
            checkpoint_path: Path to model checkpoint
        
        Returns:
            Size information dictionary
        """
        checkpoint_path = Path(checkpoint_path)
        
        if checkpoint_path.exists():
            size_bytes = checkpoint_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)
        else:
            size_bytes = 0
            size_mb = 0.0
        
        size_info = {
            'checkpoint_path': str(checkpoint_path),
            'size_bytes': int(size_bytes),
            'size_mb': float(size_mb)
        }
        
        self.results['size'] = size_info
        return size_info
    
    def measure_memory_usage(self) -> Dict[str, Any]:
        """
        Measure GPU and system memory usage.
        
        Returns:
            Memory usage dictionary
        """
        memory_info = {
            'gpu_memory_allocated': 0,
            'gpu_memory_reserved': 0,
            'gpu_memory_max_allocated': 0,
            'system_memory_used': 0,
            'system_memory_available': 0
        }
        
        if torch.cuda.is_available():
            memory_info['gpu_memory_allocated'] = torch.cuda.memory_allocated(self.device) / (1024**3)  # GB
            memory_info['gpu_memory_reserved'] = torch.cuda.memory_reserved(self.device) / (1024**3)  # GB
            memory_info['gpu_memory_max_allocated'] = torch.cuda.max_memory_allocated(self.device) / (1024**3)  # GB
        
        # System memory
        mem = psutil.virtual_memory()
        memory_info['system_memory_used'] = mem.used / (1024**3)  # GB
        memory_info['system_memory_available'] = mem.available / (1024**3)  # GB
        
        self.results['memory'] = memory_info
        return memory_info
    
    def measure_inference_speed(self, dataloader, num_batches: int = 100) -> Dict[str, Any]:
        """
        Measure inference speed.
        
        Args:
            dataloader: Data loader for inference
            num_batches: Number of batches to benchmark
        
        Returns:
            Inference speed dictionary
        """
        self.model.eval()
        
        total_samples = 0
        total_time = 0.0
        
        with torch.no_grad():
            for batch_idx, (images, _, _) in enumerate(dataloader):
                if batch_idx >= num_batches:
                    break
                
                images = images.to(self.device)
                
                # Warmup
                if batch_idx == 0:
                    _ = self.model(images)
                    if torch.cuda.is_available():
                        torch.cuda.synchronize()
                    continue
                
                # Measure
                start_time = time.time()
                _ = self.model(images)
                if torch.cuda.is_available():
                    torch.cuda.synchronize()
                end_time = time.time()
                
                total_time += (end_time - start_time)
                total_samples += images.size(0)
        
        if total_time > 0:
            samples_per_second = total_samples / total_time
            avg_time_per_sample = total_time / total_samples
            avg_time_per_batch = total_time / (num_batches - 1)  # Exclude warmup
        else:
            samples_per_second = 0.0
            avg_time_per_sample = 0.0
            avg_time_per_batch = 0.0
        
        inference_info = {
            'total_samples': int(total_samples),
            'total_time': float(total_time),
            'samples_per_second': float(samples_per_second),
            'avg_time_per_sample_ms': float(avg_time_per_sample * 1000),
            'avg_time_per_batch_ms': float(avg_time_per_batch * 1000),
            'batches_benchmarked': num_batches
        }
        
        self.results['inference'] = inference_info
        return inference_info
    
    def measure_training_epoch(self, train_fn, epoch: int) -> Dict[str, Any]:
        """
        Measure training time for one epoch.
        
        Args:
            train_fn: Training function for one epoch
            epoch: Epoch number
        
        Returns:
            Training time dictionary
        """
        start_time = time.time()
        train_fn(epoch)
        end_time = time.time()
        
        epoch_time = end_time - start_time
        
        training_info = {
            'epoch': epoch,
            'epoch_time_seconds': float(epoch_time),
            'epoch_time_minutes': float(epoch_time / 60)
        }
        
        if 'epoch_time_seconds' not in self.results['training']:
            self.results['training']['epoch_times'] = []
        self.results['training']['epoch_times'].append(training_info)
        
        return training_info
    
    def get_results(self) -> Dict[str, Any]:
        """
        Get all benchmark results.
        
        Returns:
            Complete benchmark results
        """
        return self.results
    
    def save_results(self, save_path: str):
        """
        Save benchmark results to JSON.
        
        Args:
            save_path: Path to save results
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def print_results(self):
        """Print benchmark results."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)
        
        if self.results['model_info']:
            print(f"\nModel Information:")
            print(f"  Total parameters: {self.results['model_info']['total_parameters']:,}")
            print(f"  Trainable parameters: {self.results['model_info']['trainable_parameters']:,}")
            print(f"  Non-trainable parameters: {self.results['model_info']['non_trainable_parameters']:,}")
        
        if self.results['size']:
            print(f"\nModel Size:")
            print(f"  Checkpoint: {self.results['size']['checkpoint_path']}")
            print(f"  Size: {self.results['size']['size_mb']:.2f} MB")
        
        if self.results['memory']:
            print(f"\nMemory Usage:")
            print(f"  GPU memory allocated: {self.results['memory']['gpu_memory_allocated']:.2f} GB")
            print(f"  GPU memory reserved: {self.results['memory']['gpu_memory_reserved']:.2f} GB")
            print(f"  GPU memory max allocated: {self.results['memory']['gpu_memory_max_allocated']:.2f} GB")
            print(f"  System memory used: {self.results['memory']['system_memory_used']:.2f} GB")
            print(f"  System memory available: {self.results['memory']['system_memory_available']:.2f} GB")
        
        if self.results['inference']:
            print(f"\nInference Speed:")
            print(f"  Samples per second: {self.results['inference']['samples_per_second']:.2f}")
            print(f"  Avg time per sample: {self.results['inference']['avg_time_per_sample_ms']:.2f} ms")
            print(f"  Avg time per batch: {self.results['inference']['avg_time_per_batch_ms']:.2f} ms")
            print(f"  Batches benchmarked: {self.results['inference']['batches_benchmarked']}")
        
        if self.results['training'].get('epoch_times'):
            print(f"\nTraining Times:")
            epoch_times = self.results['training']['epoch_times']
            total_time = sum(e['epoch_time_seconds'] for e in epoch_times)
            avg_time = total_time / len(epoch_times)
            print(f"  Total epochs: {len(epoch_times)}")
            print(f"  Total time: {total_time / 60:.2f} minutes")
            print(f"  Avg time per epoch: {avg_time / 60:.2f} minutes")
        
        print("\n" + "=" * 80)


def benchmark_model(
    model: nn.Module,
    device: torch.device,
    dataloader,
    checkpoint_path: str,
    save_dir: Path
) -> Dict[str, Any]:
    """
    Perform comprehensive model benchmarking.
    
    Args:
        model: Model to benchmark
        device: Device to benchmark on
        dataloader: Data loader for inference benchmarking
        checkpoint_path: Path to model checkpoint
        save_dir: Directory to save results
    
    Returns:
        Benchmark results dictionary
    """
    benchmark = Benchmark(model, device)
    
    # Measure model info
    benchmark.measure_model_info()
    
    # Measure model size
    benchmark.measure_model_size(checkpoint_path)
    
    # Measure memory usage
    benchmark.measure_memory_usage()
    
    # Measure inference speed
    benchmark.measure_inference_speed(dataloader)
    
    # Get results
    results = benchmark.get_results()
    
    # Save results
    benchmark.save_results(save_dir / 'benchmark.json')
    
    # Print results
    benchmark.print_results()
    
    return results

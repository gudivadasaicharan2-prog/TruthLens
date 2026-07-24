"""
Training Utilities
==================
Early stopping, checkpointing, and other training utilities.
"""

import torch
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
import shutil


class EarlyStopping:
    """
    Early stopping to stop training when validation loss doesn't improve.
    """
    
    def __init__(
        self,
        patience: int = 7,
        min_delta: float = 0.0,
        mode: str = 'min'
    ):
        """
        Initialize early stopping.
        
        Args:
            patience: Number of epochs to wait before stopping
            min_delta: Minimum change to qualify as an improvement
            mode: 'min' for loss, 'max' for accuracy/metric
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_score = None
        self.early_stop = False
        
        if mode == 'min':
            self.is_better = lambda score, best: score < best - min_delta
        elif mode == 'max':
            self.is_better = lambda score, best: score > best + min_delta
        else:
            raise ValueError("mode must be 'min' or 'max'")
    
    def __call__(self, score: float) -> bool:
        """
        Check if training should stop.
        
        Args:
            score: Current validation score
        
        Returns:
            True if training should stop, False otherwise
        """
        if self.best_score is None:
            self.best_score = score
            return False
        
        if self.is_better(score, self.best_score):
            self.best_score = score
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True
        
        return False
    
    def reset(self):
        """Reset the early stopping state."""
        self.counter = 0
        self.best_score = None
        self.early_stop = False


class CheckpointManager:
    """
    Manage model checkpoints during training.
    """
    
    def __init__(
        self,
        checkpoint_dir: str = 'checkpoints',
        save_best_only: bool = True,
        max_checkpoints: int = 3
    ):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_dir: Directory to save checkpoints
            save_best_only: Whether to save only the best model
            max_checkpoints: Maximum number of checkpoints to keep
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.save_best_only = save_best_only
        self.max_checkpoints = max_checkpoints
        self.best_score = None
        self.checkpoint_history = []
    
    def save(
        self,
        model: torch.nn.Module,
        optimizer: torch.optim.Optimizer,
        epoch: int,
        score: float,
        scheduler: Optional[Any] = None,
        extra_state: Optional[Dict] = None
    ) -> str:
        """
        Save a checkpoint.
        
        Args:
            model: Model to save
            optimizer: Optimizer state
            epoch: Current epoch
            score: Validation score (for best model tracking)
            scheduler: Optional learning rate scheduler
            extra_state: Additional state to save
        
        Returns:
            Path to saved checkpoint
        """
        # Determine if this is the best model
        is_best = False
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            is_best = True
        
        # Skip if not best and save_best_only is True
        if self.save_best_only and not is_best:
            return ""
        
        # Create checkpoint state
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'score': score,
            'is_best': is_best
        }
        
        if scheduler is not None:
            checkpoint['scheduler_state_dict'] = scheduler.state_dict()
        
        if extra_state is not None:
            checkpoint.update(extra_state)
        
        # Save checkpoint
        if is_best:
            checkpoint_path = self.checkpoint_dir / 'best_model.pth'
        else:
            checkpoint_path = self.checkpoint_dir / f'checkpoint_epoch_{epoch}.pth'
        
        torch.save(checkpoint, checkpoint_path)
        self.checkpoint_history.append(checkpoint_path)
        
        # Save latest checkpoint
        latest_path = self.checkpoint_dir / 'latest_checkpoint.pth'
        shutil.copy2(checkpoint_path, latest_path)
        
        # Remove old checkpoints if exceeding max
        if len(self.checkpoint_history) > self.max_checkpoints:
            old_checkpoint = self.checkpoint_history.pop(0)
            if old_checkpoint.exists() and old_checkpoint != latest_path:
                old_checkpoint.unlink()
        
        print(f"[CheckpointManager] Saved checkpoint to {checkpoint_path}")
        return str(checkpoint_path)
    
    def load(
        self,
        model: torch.nn.Module,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[Any] = None,
        checkpoint_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load a checkpoint.
        
        Args:
            model: Model to load state into
            optimizer: Optional optimizer to load state into
            scheduler: Optional scheduler to load state into
            checkpoint_path: Path to checkpoint (uses latest if None)
        
        Returns:
            Dict with checkpoint information
        """
        if checkpoint_path is None:
            checkpoint_path = self.checkpoint_dir / 'latest_checkpoint.pth'
        else:
            checkpoint_path = Path(checkpoint_path)
        
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        checkpoint = torch.load(checkpoint_path, map_location='cpu')
        
        model.load_state_dict(checkpoint['model_state_dict'])
        
        if optimizer is not None and 'optimizer_state_dict' in checkpoint:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        if scheduler is not None and 'scheduler_state_dict' in checkpoint:
            scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        print(f"[CheckpointManager] Loaded checkpoint from {checkpoint_path}")
        print(f"  Epoch: {checkpoint['epoch']}")
        print(f"  Score: {checkpoint['score']:.4f}")
        
        return checkpoint
    
    def get_best_checkpoint(self) -> Optional[Path]:
        """
        Get the path to the best checkpoint.
        
        Returns:
            Path to best checkpoint or None if not found
        """
        best_path = self.checkpoint_dir / 'best_model.pth'
        if best_path.exists():
            return best_path
        return None
    
    def save_training_config(self, config: Dict[str, Any]):
        """
        Save training configuration to checkpoint directory.
        
        Args:
            config: Training configuration dictionary
        """
        config_path = self.checkpoint_dir / 'training_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"[CheckpointManager] Saved training config to {config_path}")
    
    def load_training_config(self) -> Dict[str, Any]:
        """
        Load training configuration from checkpoint directory.
        
        Returns:
            Training configuration dictionary
        """
        config_path = self.checkpoint_dir / 'training_config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}


class AverageMeter:
    """Computes and stores the average and current value."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all statistics."""
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0
    
    def update(self, val: float, n: int = 1):
        """
        Update statistics.
        
        Args:
            val: New value
            n: Number of items
        """
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count


def get_lr(optimizer: torch.optim.Optimizer) -> float:
    """
    Get current learning rate from optimizer.
    
    Args:
        optimizer: PyTorch optimizer
    
    Returns:
        Current learning rate
    """
    for param_group in optimizer.param_groups:
        return param_group['lr']
    return 0.0


def set_seed(seed: int = 42):
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Random seed
    """
    import random
    import numpy as np
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    
    # For deterministic behavior (may impact performance)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    
    print(f"[Utils] Set random seed to {seed}")


def count_parameters(model: torch.nn.Module) -> int:
    """
    Count the number of trainable parameters in a model.
    
    Args:
        model: PyTorch model
    
    Returns:
        Number of trainable parameters
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def get_device() -> torch.device:
    """
    Get the best available device.
    
    Returns:
        torch.device (cuda if available, else cpu)
    """
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f"[Utils] Using CUDA device: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device('cpu')
        print("[Utils] Using CPU device")
    return device

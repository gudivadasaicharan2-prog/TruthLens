"""
AI Image Detection Trainer
===========================
Training pipeline for the AI image detection classifier.
"""

import os
import time
from pathlib import Path
from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.amp import autocast, GradScaler
from torch.optim.lr_scheduler import ReduceLROnPlateau, CosineAnnealingLR
import numpy as np

from app.ai.models.image_model import DeepfakeClassifierHead
from torchvision.models import efficientnet_b2, EfficientNet_B2_Weights


class AIDetectionModel(nn.Module):
    """
    Complete model for AI image detection: EfficientNet-B4 backbone + classifier head.
    """
    
    def __init__(self, backbone_frozen: bool = True):
        super().__init__()
        
        # Load EfficientNet-B4
        full_model = efficientnet_b2(
    weights=EfficientNet_B2_Weights.IMAGENET1K_V1
)
        
        # Create backbone (features + avgpool + flatten)
        self.backbone = nn.Sequential(
            full_model.features,
            full_model.avgpool,
            nn.Flatten()
        )
        
        # Freeze backbone if requested
        if backbone_frozen:
            for param in self.backbone.parameters():
                param.requires_grad = False
        
        # Classifier head
        self.classifier_head = DeepfakeClassifierHead(in_features=1408)
    
    def forward(self, x):
        features = self.backbone(x)
        output = self.classifier_head(features)
        return output


class AIDetectionTrainer:
    """
    Trainer for AI image detection classifier.
    """
    
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        learning_rate: float = 3e-4,
        weight_decay: float = 1e-5,
        checkpoint_dir: str = None,
        log_interval: int = 100,
        t_max: int = 10
    ):
        """
        Initialize trainer.
        
        Args:
            model: The model to train
            train_loader: Training data loader
            val_loader: Validation data loader
            device: Device to train on
            learning_rate: Learning rate
            weight_decay: Weight decay for optimizer
            checkpoint_dir: Directory to save checkpoints
            log_interval: Interval for logging training progress
            t_max: Maximum number of epochs for CosineAnnealingLR scheduler
        """
        self.model = model.to(device)
        self.scaler = GradScaler()
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        self.log_interval = log_interval
        
        # Create checkpoint directory
        if self.checkpoint_dir:
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Loss function (binary classification)
        self.criterion = nn.BCEWithLogitsLoss()
        
        # Optimizer (AdamW)
        self.optimizer = optim.AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        # Learning rate scheduler
        self.scheduler = CosineAnnealingLR(
            self.optimizer,
            T_max=t_max
        )
        
        # Training history
        self.history = {
            'train_loss': [],
            'train_acc': [],
            'val_loss': [],
            'val_acc': [],
            'learning_rate': []
        }
        
        self.best_val_loss = float('inf')
        self.best_val_acc = 0.0
        self.epoch = 0
        
        # Enable cuDNN benchmark for optimized performance
        if torch.cuda.is_available():
            torch.backends.cudnn.benchmark = True
        
        # Print GPU information
        print(f"[Trainer] GPU Information:")
        print(f"  GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
        print(f"  CUDA Available: {torch.cuda.is_available()}")
        print(f"  CUDA Version: {torch.version.cuda if torch.cuda.is_available() else 'N/A'}")
        print(f"  Current Device: {device}")
        print(f"[Trainer] Train batches: {len(train_loader)}")
        print(f"[Trainer] Val batches: {len(val_loader)}")
    
    def train_epoch(self) -> Tuple[float, float]:
        """
        Train for one epoch.
        
        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0
        
        for batch_idx, (images, labels) in enumerate(self.train_loader):
            images = images.to(self.device, non_blocking=True)
            labels = labels.float().to(self.device, non_blocking=True)
            
            # Forward pass with AMP
            self.optimizer.zero_grad()
            with autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
                outputs = self.model(images)
                loss = self.criterion(outputs.squeeze(), labels)
            
            # Backward pass with AMP
            self.scaler.scale(loss).backward()
            self.scaler.step(self.optimizer)
            self.scaler.update()
            
            # Statistics
            total_loss += loss.item()
            predicted = (torch.sigmoid(outputs.squeeze()) > 0.5).float()
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
            # Log progress
            if batch_idx % self.log_interval == 0:
                print(f"[Train] Epoch {self.epoch} [{batch_idx}/{len(self.train_loader)}] "
                      f"Loss: {loss.item():.4f} Acc: {100.*correct/total:.2f}%")
        
        avg_loss = total_loss / len(self.train_loader)
        accuracy = 100. * correct / total
        
        return avg_loss, accuracy
    
    def validate(self) -> Tuple[float, float]:
        """
        Validate the model.
        
        Returns:
            Tuple of (average_loss, accuracy)
        """
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for images, labels in self.val_loader:
                images = images.to(self.device, non_blocking=True)
                labels = labels.float().to(self.device, non_blocking=True)
                
                # Forward pass with AMP
                with autocast(device_type='cuda' if torch.cuda.is_available() else 'cpu'):
                    outputs = self.model(images)
                    loss = self.criterion(outputs.squeeze(), labels)
                
                # Statistics
                total_loss += loss.item()
                predicted = (torch.sigmoid(outputs.squeeze()) > 0.5).float()
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        avg_loss = total_loss / len(self.val_loader)
        accuracy = 100. * correct / total
        
        return avg_loss, accuracy
    
    def save_checkpoint(
        self,
        filename: str,
        is_best: bool = False,
        save_optimizer: bool = True,
        save_inference_weights: bool = True
    ):
        """
        Save model checkpoint.
        
        Args:
            filename: Checkpoint filename
            is_best: Whether this is the best model so far
            save_optimizer: Whether to save optimizer state
            save_inference_weights: Whether to save classifier head only for inference
        """
        if not self.checkpoint_dir:
            print("[Trainer] No checkpoint directory set, skipping save")
            return
        
        checkpoint = {
            'epoch': self.epoch,
            'model_state_dict': self.model.state_dict(),
            'val_loss': self.history['val_loss'][-1] if self.history['val_loss'] else 0,
            'val_acc': self.history['val_acc'][-1] if self.history['val_acc'] else 0,
            'history': self.history
        }
        
        if save_optimizer:
            checkpoint['optimizer_state_dict'] = self.optimizer.state_dict()
            checkpoint['scheduler_state_dict'] = self.scheduler.state_dict()
        
        checkpoint_path = self.checkpoint_dir / filename
        torch.save(checkpoint, checkpoint_path)
        print(f"[Trainer] Saved checkpoint to {checkpoint_path}")
        
        if is_best:
            best_path = self.checkpoint_dir / 'best_model.pth'
            torch.save(checkpoint, best_path)
            print(f"[Trainer] Saved best model to {best_path}")
        
        # Save classifier head only for inference compatibility
        if save_inference_weights and is_best:
            # Extract only the classifier head state dict
            classifier_state = {}
            for key, value in self.model.state_dict().items():
                if key.startswith('classifier_head.'):
                    classifier_state[key.replace('classifier_head.', '')] = value
            
            # Save to weights directory for automatic loading by image_model
            weights_dir = self.checkpoint_dir.parent.parent / 'weights'
            weights_dir.mkdir(parents=True, exist_ok=True)
            inference_path = weights_dir / 'deepfake_classifier.pth'
            torch.save(classifier_state, inference_path)
            print(f"[Trainer] Saved inference weights to {inference_path}")
    
    def load_checkpoint(self, checkpoint_path: str, load_optimizer: bool = True):
        """
        Load model checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file
            load_optimizer: Whether to load optimizer state
        """
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        # Check checkpoint compatibility with current model
        model_state = checkpoint['model_state_dict']
        
        # Check if checkpoint is from EfficientNet-B4 (1792 features) vs B2 (1408 features)
        # by checking the fc1 layer input dimension
        if 'classifier_head.fc1.weight' in model_state:
            fc1_shape = model_state['classifier_head.fc1.weight'].shape[1]
            current_fc1_shape = self.model.classifier_head.fc1.in_features
            
            if fc1_shape != current_fc1_shape:
                print(f"[Trainer] WARNING: Checkpoint incompatible with current model")
                print(f"[Trainer] Checkpoint fc1 input dim: {fc1_shape}")
                print(f"[Trainer] Current model fc1 input dim: {current_fc1_shape}")
                print(f"[Trainer] Skipping checkpoint load to start fresh training")
                return
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.epoch = checkpoint.get('epoch', 0) + 1
        self.history = checkpoint.get('history', self.history)
        
        if load_optimizer and 'optimizer_state_dict' in checkpoint:
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        
        if load_optimizer and 'scheduler_state_dict' in checkpoint:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
        print(f"[Trainer] Loaded checkpoint from {checkpoint_path}")
        print(f"[Trainer] Resumed from epoch {self.epoch}")
    
    def train(
    self,
    num_epochs: int,
    early_stopping_patience: int = 15,
    save_interval: int = 1
):
        """
        Train the model for multiple epochs.
        
        Args:
            num_epochs: Number of epochs to train
            early_stopping_patience: Patience for early stopping
            save_interval: Interval for saving checkpoints
        """
        print(f"[Trainer] Starting training for {num_epochs} epochs")
        print(f"[Trainer] Early stopping patience: {early_stopping_patience}")
        
        patience_counter = 0
        
        for epoch in range(self.epoch, self.epoch + num_epochs):
            self.epoch = epoch
            epoch_start_time = time.time()
            
            # Train
            train_loss, train_acc = self.train_epoch()
            
            # Validate
            val_loss, val_acc = self.validate()
            
            # Update learning rate
            self.scheduler.step()
            current_lr = self.optimizer.param_groups[0]['lr']
            
            # Record history
            self.history['train_loss'].append(train_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_loss'].append(val_loss)
            self.history['val_acc'].append(val_acc)
            self.history['learning_rate'].append(current_lr)
            
            # Print epoch summary
            epoch_time = time.time() - epoch_start_time
            print(f"[Epoch {epoch}] "
                  f"Train Loss: {train_loss:.4f} Acc: {train_acc:.2f}% | "
                  f"Val Loss: {val_loss:.4f} Acc: {val_acc:.2f}% | "
                  f"LR: {current_lr:.6f} | Time: {epoch_time:.2f}s")
            
            # Check if best model
            is_best = val_acc > self.best_val_acc
            if is_best:
                self.best_val_acc = val_acc
                self.best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
            
            # Save checkpoint
            if (epoch + 1) % save_interval == 0 or is_best:
                self.save_checkpoint(
                    f'checkpoint_epoch_{epoch}.pth',
                    is_best=is_best
                )
            
            # Early stopping
            if patience_counter >= early_stopping_patience:
                print(f"[Trainer] Early stopping triggered after {epoch + 1} epochs")
                break
        
        # Save final model
        self.save_checkpoint('final_model.pth', is_best=True)
        
        print(f"[Trainer] Training complete")
        print(f"[Trainer] Best validation accuracy: {self.best_val_acc:.2f}%")
        print(f"[Trainer] Best validation loss: {self.best_val_loss:.4f}")

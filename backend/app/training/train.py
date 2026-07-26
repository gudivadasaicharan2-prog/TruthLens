"""
TruthLens Training Script
=========================
Train AI content detection models with configurable parameters.
"""

import argparse
import yaml
import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter
from pathlib import Path
from typing import Dict, Any
import sys
import os
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.dataset import TruthLensDataset
from app.training.dataloader import create_data_loaders, get_default_transforms
from app.training.models import create_model, get_model_info
from app.training.utils import (
    EarlyStopping, CheckpointManager, AverageMeter,
    get_lr, set_seed, count_parameters, get_device
)
from app.training.experiment_manager import ExperimentManager
from app.training.data_validator import DataValidator
try:
    from app.training.plotting import generate_all_plots
except ImportError:
    print("[Warning] Matplotlib unavailable. Training plots will be skipped.")
    generate_all_plots = None


def train_epoch(
    model: nn.Module,
    train_loader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int,
    scaler: torch.amp.GradScaler,
    use_amp: bool = True,
    writer: SummaryWriter = None
) -> Dict[str, float]:
    """
    Train for one epoch.
    
    Args:
        model: Model to train
        train_loader: Training data loader
        criterion: Loss function
        optimizer: Optimizer
        device: Device to train on
        epoch: Current epoch number
        scaler: GradScaler for mixed precision
        use_amp: Whether to use automatic mixed precision
        writer: TensorBoard writer
    
    Returns:
        Dict with training metrics
    """
    model.train()
    
    losses = AverageMeter()
    accuracies = AverageMeter()
    
    progress_bar = tqdm(
        train_loader,
        desc=f"Epoch {epoch+1}",
        leave=False
    )

    for batch_idx, (images, labels, _) in enumerate(progress_bar):
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        
        optimizer.zero_grad()
        
        if use_amp:
            with torch.amp.autocast("cuda"):
                outputs = model(images)
                loss = criterion(outputs, labels)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
        
        # Calculate accuracy
        _, predicted = torch.max(outputs, 1)
        accuracy = (predicted == labels).float().mean()
        
        losses.update(loss.item(), images.size(0))
        accuracies.update(accuracy.item(), images.size(0))
        
        # Update progress bar
        progress_bar.set_postfix(
            loss=f"{loss.item():.4f}",
            acc=f"{accuracies.avg:.4f}",
            lr=f"{get_lr(optimizer):.6f}"
        )
        
        # Log to TensorBoard
        if writer is not None and batch_idx % 100 == 0:
            global_step = epoch * len(train_loader) + batch_idx
            writer.add_scalar('Train/BatchLoss', loss.item(), global_step)
            writer.add_scalar('Train/BatchAccuracy', accuracy.item(), global_step)
            writer.add_scalar('Train/LearningRate', get_lr(optimizer), global_step)
    
    return {
        'loss': losses.avg,
        'accuracy': accuracies.avg
    }


def validate(
    model: nn.Module,
    val_loader,
    criterion: nn.Module,
    device: torch.device,
    epoch: int,
    writer: SummaryWriter = None
) -> Dict[str, float]:
    """
    Validate the model.
    
    Args:
        model: Model to validate
        val_loader: Validation data loader
        criterion: Loss function
        device: Device to validate on
        epoch: Current epoch number
        writer: TensorBoard writer
    
    Returns:
        Dict with validation metrics
    """
    model.eval()
    
    losses = AverageMeter()
    accuracies = AverageMeter()
    
    all_preds = []
    all_labels = []
    all_metadata = []
    
    with torch.no_grad():
        progress_bar = tqdm(val_loader, desc="Validating", leave=False)
        for images, labels, metadata in progress_bar:
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)
            
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            # Calculate accuracy
            _, predicted = torch.max(outputs, 1)
            accuracy = (predicted == labels).float().mean()
            
            losses.update(loss.item(), images.size(0))
            accuracies.update(accuracy.item(), images.size(0))
            
            # Store predictions for detailed metrics
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_metadata.extend(metadata)
    
    # Log to TensorBoard
    if writer is not None:
        writer.add_scalar('Val/Loss', losses.avg, epoch)
        writer.add_scalar('Val/Accuracy', accuracies.avg, epoch)
    
    return {
        'loss': losses.avg,
        'accuracy': accuracies.avg,
        'predictions': all_preds,
        'labels': all_labels,
        'metadata': all_metadata
    }


def train(config: Dict[str, Any]):
    """
    Main training function.
    
    Args:
        config: Training configuration dictionary
    """
    # Set seed for reproducibility
    if config.get('seed'):
        set_seed(config['seed'])
    
    # Get device
    device = get_device()
    
    # Create experiment manager
    experiment_manager = ExperimentManager(
        base_dir=config.get('experiment', {}).get('base_dir', 'experiments')
    )
    
    # Validate metadata before training
    if config.get('experiment', {}).get('validate_data', True):
        print(f"\n[Train] Validating metadata...")
        validator = DataValidator(
            metadata_path=config['data']['train_metadata'],
            dataset_dir=config['data']['dataset_dir']
        )
        validation_report = validator.validate()
        validator.print_report(validation_report)
        
        if not validation_report['is_valid']:
            print(f"[Train] ERROR: Data validation failed. Please fix the errors above.")
            return
        
        # Save validation report
        if config.get('experiment', {}).get('save_validation_report', True):
            validation_report_path = Path(config['data']['dataset_dir']) / 'validation_report.json'
            validator.save_report(validation_report, validation_report_path)
    
    # Create experiment
    experiment_id = experiment_manager.create_experiment(
        config=config,
        experiment_name=config.get('experiment', {}).get('name', None)
    )
    
    # Update experiment status to running
    experiment_manager.update_experiment_status(experiment_id, 'running')
    
    # Get experiment directories
    checkpoint_dir = experiment_manager.get_checkpoint_dir(experiment_id)
    log_dir = experiment_manager.get_log_dir(experiment_id)
    plots_dir = experiment_manager.get_plots_dir(experiment_id)
    
    print(f"[Train] Experiment ID: {experiment_id}")
    print(f"[Train] Checkpoint directory: {checkpoint_dir}")
    print(f"[Train] Log directory: {log_dir}")
    print(f"[Train] Plots directory: {plots_dir}")
    
    # Create model
    print(f"\n[Train] Creating model: {config['model']['architecture']}")
    model = create_model(
        architecture=config['model']['architecture'],
        num_classes=config['model']['num_classes'],
        pretrained=config['model']['pretrained'],
        dropout=config['model'].get('dropout', 0.3),
        freeze_backbone=config['model'].get('freeze_backbone', False)
    )
    model = model.to(device)
    
    print(f"[Train] Model parameters: {count_parameters(model):,}")
    
    # Create data loaders
    print(f"\n[Train] Creating data loaders...")
    train_transform, val_transform = get_default_transforms(
        image_size=config['data']['image_size'],
        augment=config['data'].get('augment', True)
    )
    
    data_loaders = create_data_loaders(
        train_metadata=config['data']['train_metadata'],
        val_metadata=config['data']['val_metadata'],
        dataset_dir=config['data']['dataset_dir'],
        batch_size=config['data']['batch_size'],
        num_workers=config['data'].get('num_workers', 4),
        pin_memory=config['data'].get('pin_memory', True),
        train_transform=train_transform,
        val_transform=val_transform,
        balanced_sampling=config['data'].get('balanced_sampling', True),
        samples_per_generator=config['data'].get('samples_per_generator', None),
        deterministic=config.get('deterministic', False)
    )
    
    train_loader = data_loaders['train']
    val_loader = data_loaders['val']
    
    # Create loss function
    criterion = nn.CrossEntropyLoss()
    if config['training'].get('class_weights'):
        class_weights = torch.tensor(config['training']['class_weights']).to(device)
        criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    # Create optimizer
    optimizer_config = config['training']['optimizer']
    if optimizer_config['type'] == 'adam':
        optimizer = torch.optim.Adam(
            model.parameters(),
            lr=optimizer_config['lr'],
            weight_decay=optimizer_config.get('weight_decay', 0.0)
        )
    elif optimizer_config['type'] == 'adamw':
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=optimizer_config['lr'],
            weight_decay=optimizer_config.get('weight_decay', 0.01)
        )
    elif optimizer_config['type'] == 'sgd':
        optimizer = torch.optim.SGD(
            model.parameters(),
            lr=optimizer_config['lr'],
            momentum=optimizer_config.get('momentum', 0.9),
            weight_decay=optimizer_config.get('weight_decay', 0.0)
        )
    else:
        raise ValueError(f"Unknown optimizer: {optimizer_config['type']}")
    
    # Create learning rate scheduler
    scheduler_config = config['training'].get('scheduler', {})
    if scheduler_config:
        if scheduler_config['type'] == 'step':
            scheduler = torch.optim.lr_scheduler.StepLR(
                optimizer,
                step_size=scheduler_config['step_size'],
                gamma=scheduler_config.get('gamma', 0.1)
            )
        elif scheduler_config['type'] == 'cosine':
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=scheduler_config.get('T_max', config['training']['epochs'])
            )
        elif scheduler_config['type'] == 'plateau':
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer,
                mode='max',
                factor=scheduler_config.get('factor', 0.1),
                patience=scheduler_config.get('patience', 5)
            )
        else:
            scheduler = None
    else:
        scheduler = None
    
    # Create checkpoint manager with experiment directory
    checkpoint_manager = CheckpointManager(
        checkpoint_dir=str(checkpoint_dir),
        save_best_only=config['training'].get('save_best_only', True),
        max_checkpoints=config['training'].get('max_checkpoints', 3)
    )
    
    # Create early stopping
    early_stopping = None
    early_stopping_config = config['training'].get('early_stopping', {})
    if isinstance(early_stopping_config, dict) and early_stopping_config.get('enabled', False):
        early_stopping = EarlyStopping(
            patience=early_stopping_config.get('patience', 7),
            min_delta=early_stopping_config.get('min_delta', 0.0),
            mode='max'  # We want to maximize accuracy
        )
    
    # Create TensorBoard writer with experiment directory
    writer = None
    if config['training'].get('use_tensorboard', True):
        writer = SummaryWriter(log_dir=log_dir)
        print(f"[Train] TensorBoard logs: {log_dir}")
    
    # Create gradient scaler for mixed precision
    use_amp = config['training'].get('mixed_precision', False)
    scaler = torch.amp.GradScaler("cuda") if use_amp else None
    
    # Resume from checkpoint if specified
    start_epoch = 0
    if config['training'].get('resume'):
        print(f"[Train] Resuming from checkpoint...")
        checkpoint = checkpoint_manager.load(model, optimizer, scheduler)
        start_epoch = checkpoint['epoch'] + 1
        if early_stopping:
            early_stopping.best_score = checkpoint.get('score', 0)
    
    # Training loop
    num_epochs = config['training']['epochs']
    best_val_accuracy = 0.0
    best_epoch = 0
    
    # Training history
    history = {
        'train_loss': [],
        'train_accuracy': [],
        'val_loss': [],
        'val_accuracy': []
    }
    
    print(f"\n[Train] Starting training for {num_epochs} epochs...")
    print(f"[Train] Mixed precision: {use_amp}")
    print(f"[Train] Starting epoch: {start_epoch}")
    
    for epoch in range(start_epoch, num_epochs):
        print(f"\n[Train] Epoch {epoch + 1}/{num_epochs}")
        print(f"[Train] Learning rate: {get_lr(optimizer):.6f}")
        
        # Train
        train_metrics = train_epoch(
            model=model,
            train_loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
            epoch=epoch,
            scaler=scaler,
            use_amp=use_amp,
            writer=writer
        )
        
        print(f"[Train] Train Loss: {train_metrics['loss']:.4f}")
        print(f"[Train] Train Accuracy: {train_metrics['accuracy']:.4f}")
        
        # Validate
        val_metrics = validate(
            model=model,
            val_loader=val_loader,
            criterion=criterion,
            device=device,
            epoch=epoch,
            writer=writer
        )
        
        print(f"[Train] Val Loss: {val_metrics['loss']:.4f}")
        print(f"[Train] Val Accuracy: {val_metrics['accuracy']:.4f}")
        
        # Update training history
        history['train_loss'].append(train_metrics['loss'])
        history['train_accuracy'].append(train_metrics['accuracy'])
        history['val_loss'].append(val_metrics['loss'])
        history['val_accuracy'].append(val_metrics['accuracy'])
        
        # Update learning rate scheduler
        if scheduler:
            if isinstance(scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                scheduler.step(val_metrics['accuracy'])
            else:
                scheduler.step()
        
        # Save checkpoint
        checkpoint_manager.save(
            model=model,
            optimizer=optimizer,
            epoch=epoch,
            score=val_metrics['accuracy'],
            scheduler=scheduler
        )
        
        # Update best accuracy
        if val_metrics['accuracy'] > best_val_accuracy:
            best_val_accuracy = val_metrics['accuracy']
            best_epoch = epoch
            print(f"[Train] New best validation accuracy: {best_val_accuracy:.4f} at epoch {epoch + 1}")
        
        # Early stopping
        if early_stopping:
            if early_stopping(val_metrics['accuracy']):
                print(f"[Train] Early stopping triggered at epoch {epoch + 1}")
                break
    
    # Reload best checkpoint before exiting
    best_checkpoint_path = checkpoint_manager.get_best_checkpoint()
    if best_checkpoint_path:
        print(f"\n[Train] Reloading best checkpoint from {best_checkpoint_path}")
        checkpoint_manager.load(model, optimizer, scheduler, str(best_checkpoint_path))
        print(f"[Train] Best model restored (val accuracy: {best_val_accuracy:.4f})")
    else:
        print(f"[Train] Warning: No best checkpoint found to reload")
    
    # Close TensorBoard writer
    if writer:
        writer.close()
    
    # Save training history
    if config.get('experiment', {}).get('save_history', True):
        experiment_manager.save_training_history(experiment_id, history)
        print(f"[Train] Training history saved")
    
    # Generate plots
    if (
        config.get('experiment', {}).get('save_plots', True)
        and generate_all_plots is not None
    ):
        print(f"[Train] Generating training plots...")
        generate_all_plots(history, val_metrics, plots_dir)
    
    # Update experiment registry with final metrics
    final_metrics = {
        'accuracy': best_val_accuracy,
        'precision': 0.0,  # Would need full validation to compute
        'recall': 0.0,     # Would need full validation to compute
        'f1': 0.0,         # Would need full validation to compute
        'roc_auc': 0.0     # Would need full validation to compute
    }
    
    experiment_manager.update_experiment_status(
        experiment_id,
        'completed',
        metrics=final_metrics,
        best_epoch=best_epoch
    )
    
    # Update checkpoint path in registry
    if best_checkpoint_path:
        experiment_manager.update_checkpoint_path(experiment_id, str(best_checkpoint_path))
    
    print(f"\n[Train] Training complete!")
    print(f"[Train] Experiment ID: {experiment_id}")
    print(f"[Train] Best validation accuracy: {best_val_accuracy:.4f} at epoch {best_epoch + 1}")
    print(f"[Train] Best checkpoint: {best_checkpoint_path}")
    print(f"[Train] Experiment directory: {experiment_manager.get_experiment_dir(experiment_id)}")


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load training configuration from YAML file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Train TruthLens AI detection model')
    parser.add_argument('--config', type=str, required=True, help='Path to training config file')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override resume if specified
    if args.resume:
        config['training']['resume'] = True
    
    # Run training
    train(config)


if __name__ == '__main__':
    main()

"""
TruthLens Validation Script
===========================
Validate AI content detection models with comprehensive metrics.
"""

import argparse
import yaml
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    average_precision_score
)
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.dataset import TruthLensDataset
from app.training.dataloader import get_default_transforms
from app.training.models import create_model
from app.training.utils import get_device, CheckpointManager
from app.training.error_analysis import analyze_errors
from app.training.benchmarking import benchmark_model


def validate_model(
    model: nn.Module,
    val_loader,
    device: torch.device,
    criterion: nn.Module = None
) -> Dict[str, Any]:
    """
    Validate model and compute comprehensive metrics.
    
    Args:
        model: Model to validate
        val_loader: Validation data loader
        device: Device to validate on
        criterion: Optional loss function
    
    Returns:
        Dict with validation metrics
    """
    model.eval()
    
    all_preds = []
    all_labels = []
    all_probs = []
    all_metadata = []
    total_loss = 0.0
    total_samples = 0
    
    with torch.no_grad():
        for images, labels, metadata in val_loader:
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = torch.max(outputs, 1)
            
            if criterion:
                loss = criterion(outputs, labels)
                total_loss += loss.item() * images.size(0)
                total_samples += images.size(0)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            all_metadata.extend(metadata)
    
    # Convert to numpy arrays
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    all_probs = np.array(all_probs)
    
    # Calculate basic metrics
    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average='binary', zero_division=0)
    recall = recall_score(all_labels, all_preds, average='binary', zero_division=0)
    f1 = f1_score(all_labels, all_preds, average='binary', zero_division=0)
    
    # Calculate ROC-AUC
    try:
        roc_auc = roc_auc_score(all_labels, all_probs[:, 1])
    except:
        roc_auc = 0.0
    
    # Calculate PR-AUC
    try:
        pr_auc = average_precision_score(all_labels, all_probs[:, 1])
    except:
        pr_auc = 0.0
    
    # Calculate confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    
    # Calculate per-generator metrics
    generator_metrics = calculate_per_generator_metrics(
        all_preds, all_labels, all_metadata
    )
    
    # Calculate per-dataset metrics
    dataset_metrics = calculate_per_dataset_metrics(
        all_preds, all_labels, all_metadata
    )
    
    # Calculate per-label metrics
    label_metrics = calculate_per_label_metrics(all_preds, all_labels)
    
    results = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'roc_auc': roc_auc,
        'pr_auc': pr_auc,
        'confusion_matrix': cm.tolist(),
        'loss': total_loss / total_samples if total_samples > 0 else 0.0,
        'num_samples': len(all_labels),
        'generator_metrics': generator_metrics,
        'dataset_metrics': dataset_metrics,
        'label_metrics': label_metrics,
        'classification_report': classification_report(
            all_labels, all_preds, target_names=['real', 'ai'], output_dict=True
        )
    }
    
    return results


def calculate_per_generator_metrics(
    preds: np.ndarray,
    labels: np.ndarray,
    metadata: List[Dict]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate metrics per AI generator.
    
    Args:
        preds: Predictions
        labels: Ground truth labels
        metadata: Sample metadata
    
    Returns:
        Dict mapping generator to metrics
    """
    generator_metrics = {}
    
    # Group by generator
    generator_data = default_dict(list)
    for pred, label, meta in zip(preds, labels, metadata):
        if meta['label'].lower() == 'ai':
            generator = meta.get('generator', 'unknown')
            generator_data[generator].append((pred, label))
    
    # Calculate metrics per generator
    for generator, data in generator_data.items():
        gen_preds = np.array([d[0] for d in data])
        gen_labels = np.array([d[1] for d in data])
        
        if len(gen_labels) > 0:
            generator_metrics[generator] = {
                'accuracy': accuracy_score(gen_labels, gen_preds),
                'precision': precision_score(gen_labels, gen_preds, zero_division=0),
                'recall': recall_score(gen_labels, gen_preds, zero_division=0),
                'f1': f1_score(gen_labels, gen_preds, zero_division=0),
                'num_samples': len(gen_labels)
            }
    
    return generator_metrics


def calculate_per_dataset_metrics(
    preds: np.ndarray,
    labels: np.ndarray,
    metadata: List[Dict]
) -> Dict[str, Dict[str, float]]:
    """
    Calculate metrics per source dataset.
    
    Args:
        preds: Predictions
        labels: Ground truth labels
        metadata: Sample metadata
    
    Returns:
        Dict mapping dataset to metrics
    """
    from collections import defaultdict
    
    dataset_metrics = {}
    
    # Group by dataset
    dataset_data = defaultdict(list)
    for pred, label, meta in zip(preds, labels, metadata):
        dataset = meta.get('source_dataset', 'unknown')
        dataset_data[dataset].append((pred, label))
    
    # Calculate metrics per dataset
    for dataset, data in dataset_data.items():
        ds_preds = np.array([d[0] for d in data])
        ds_labels = np.array([d[1] for d in data])
        
        if len(ds_labels) > 0:
            dataset_metrics[dataset] = {
                'accuracy': accuracy_score(ds_labels, ds_preds),
                'precision': precision_score(ds_labels, ds_preds, zero_division=0),
                'recall': recall_score(ds_labels, ds_preds, zero_division=0),
                'f1': f1_score(ds_labels, ds_preds, zero_division=0),
                'num_samples': len(ds_labels)
            }
    
    return dataset_metrics


def calculate_per_label_metrics(
    preds: np.ndarray,
    labels: np.ndarray
) -> Dict[str, Dict[str, float]]:
    """
    Calculate metrics per label (real vs AI).
    
    Args:
        preds: Predictions
        labels: Ground truth labels
    
    Returns:
        Dict mapping label to metrics
    """
    label_metrics = {}
    
    for label_idx, label_name in enumerate(['real', 'ai']):
        mask = labels == label_idx
        if mask.sum() > 0:
            label_preds = preds[mask]
            label_labels = labels[mask]
            
            label_metrics[label_name] = {
                'accuracy': accuracy_score(label_labels, label_preds),
                'num_samples': mask.sum()
            }
    
    return label_metrics


def print_metrics(results: Dict[str, Any]):
    """
    Print validation metrics in a readable format.
    
    Args:
        results: Validation results dictionary
    """
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    
    print(f"\nOverall Metrics:")
    print(f"  Accuracy:  {results['accuracy']:.4f}")
    print(f"  Precision: {results['precision']:.4f}")
    print(f"  Recall:    {results['recall']:.4f}")
    print(f"  F1 Score:  {results['f1']:.4f}")
    print(f"  ROC-AUC:   {results['roc_auc']:.4f}")
    print(f"  PR-AUC:    {results['pr_auc']:.4f}")
    print(f"  Loss:      {results['loss']:.4f}")
    print(f"  Samples:   {results['num_samples']}")
    
    print(f"\nConfusion Matrix:")
    cm = np.array(results['confusion_matrix'])
    print(f"  True Negatives (Real correctly identified): {cm[0, 0]}")
    print(f"  False Positives (Real misidentified as AI): {cm[0, 1]}")
    print(f"  False Negatives (AI misidentified as Real): {cm[1, 0]}")
    print(f"  True Positives (AI correctly identified):    {cm[1, 1]}")
    
    print(f"\nPer-Label Metrics:")
    for label, metrics in results['label_metrics'].items():
        print(f"  {label.capitalize()}:")
        print(f"    Accuracy: {metrics['accuracy']:.4f}")
        print(f"    Samples:  {metrics['num_samples']}")
    
    if results['generator_metrics']:
        print(f"\nPer-Generator Metrics (AI images only):")
        for generator, metrics in results['generator_metrics'].items():
            print(f"  {generator}:")
            print(f"    Accuracy:  {metrics['accuracy']:.4f}")
            print(f"    Precision: {metrics['precision']:.4f}")
            print(f"    Recall:    {metrics['recall']:.4f}")
            print(f"    F1 Score:  {metrics['f1']:.4f}")
            print(f"    Samples:   {metrics['num_samples']}")
    
    if results['dataset_metrics']:
        print(f"\nPer-Dataset Metrics:")
        for dataset, metrics in results['dataset_metrics'].items():
            print(f"  {dataset}:")
            print(f"    Accuracy:  {metrics['accuracy']:.4f}")
            print(f"    Precision: {metrics['precision']:.4f}")
            print(f"    Recall:    {metrics['recall']:.4f}")
            print(f"    F1 Score:  {metrics['f1']:.4f}")
            print(f"    Samples:   {metrics['num_samples']}")
    
    print("\n" + "=" * 80)


def save_metrics(results: Dict[str, Any], output_path: str):
    """
    Save validation metrics to JSON file.
    
    Args:
        results: Validation results dictionary
        output_path: Path to save results
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n[Metrics] Saved results to {output_path}")


def validate(config: Dict[str, Any]):
    """
    Main validation function.
    
    Args:
        config: Validation configuration dictionary
    """
    # Get device
    device = get_device()
    
    # Create model
    print(f"\n[Validate] Creating model: {config['model']['architecture']}")
    model = create_model(
        architecture=config['model']['architecture'],
        num_classes=config['model']['num_classes'],
        pretrained=False  # Load from checkpoint
    )
    model = model.to(device)
    
    # Load checkpoint
    checkpoint_path = config['validation'].get('checkpoint_path')
    if checkpoint_path:
        checkpoint_manager = CheckpointManager(
            checkpoint_dir=str(Path(checkpoint_path).parent)
        )
        checkpoint_manager.load(model, checkpoint_path=checkpoint_path)
    else:
        raise ValueError("checkpoint_path must be specified in config")
    
    # Create validation dataset
    print(f"\n[Validate] Creating validation dataset...")
    _, val_transform = get_default_transforms(
        image_size=config['data']['image_size'],
        augment=False
    )
    
    val_dataset = TruthLensDataset(
        metadata_path=config['data']['val_metadata'],
        dataset_dir=config['data']['dataset_dir'],
        split='val',
        transform=val_transform
    )
    
    # Create validation data loader
    from torch.utils.data import DataLoader
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=config['data']['batch_size'],
        shuffle=False,
        num_workers=config['data'].get('num_workers', 4),
        pin_memory=config['data'].get('pin_memory', True)
    )
    
    print(f"[Validate] Validation batches: {len(val_loader)}")
    
    # Create loss function
    criterion = nn.CrossEntropyLoss()
    
    # Validate
    print(f"\n[Validate] Running validation...")
    results = validate_model(model, val_loader, device, criterion)
    
    # Print results
    print_metrics(results)
    
    # Save results
    if config['validation'].get('output_path'):
        save_metrics(results, config['validation']['output_path'])
    
    # Error analysis
    if config['validation'].get('error_analysis', True):
        print(f"\n[Validate] Running error analysis...")
        output_dir = Path(config['validation'].get('output_path', '.')).parent
        error_analysis_results = analyze_errors(
            predictions=np.array(results['predictions']),
            labels=np.array(results['labels']),
            probabilities=np.array(results['probabilities']) if 'probabilities' in results else None,
            metadata=results['metadata'],
            save_dir=output_dir
        )
        results['error_analysis'] = error_analysis_results
    
    # Benchmarking
    if config['validation'].get('benchmark', True):
        print(f"\n[Validate] Running benchmarking...")
        output_dir = Path(config['validation'].get('output_path', '.')).parent
        checkpoint_path = config['validation'].get('checkpoint_path')
        benchmark_results = benchmark_model(
            model=model,
            device=device,
            dataloader=val_loader,
            checkpoint_path=checkpoint_path,
            save_dir=output_dir
        )
        results['benchmark'] = benchmark_results
    
    return results


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load validation configuration from YAML file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Validate TruthLens AI detection model')
    parser.add_argument('--config', type=str, required=True, help='Path to validation config file')
    parser.add_argument('--checkpoint', type=str, help='Path to model checkpoint (overrides config)')
    parser.add_argument('--output', type=str, help='Path to save results (overrides config)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override checkpoint if specified
    if args.checkpoint:
        config['validation']['checkpoint_path'] = args.checkpoint
    
    # Override output if specified
    if args.output:
        config['validation']['output_path'] = args.output
    
    # Run validation
    validate(config)


if __name__ == '__main__':
    main()

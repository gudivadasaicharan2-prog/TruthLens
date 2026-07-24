"""
TruthLens Test Script
=====================
Test trained models for inference and benchmarking.
"""

import argparse
import yaml
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import json
import sys
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.dataset import TruthLensDataset
from app.training.dataloader import get_default_transforms
from app.training.models import create_model
from app.training.utils import get_device, CheckpointManager


def test_model(
    model: nn.Module,
    test_loader: DataLoader,
    device: torch.device,
    return_probs: bool = True
) -> Dict[str, Any]:
    """
    Test model and return predictions.
    
    Args:
        model: Model to test
        test_loader: Test data loader
        device: Device to test on
        return_probs: Whether to return probabilities
    
    Returns:
        Dict with predictions and metadata
    """
    model.eval()
    
    all_preds = []
    all_labels = []
    all_probs = []
    all_metadata = []
    
    with torch.no_grad():
        for images, labels, metadata in tqdm(test_loader, desc="Testing"):
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            
            if return_probs:
                probs = torch.softmax(outputs, dim=1)
                all_probs.extend(probs.cpu().numpy())
            
            _, predicted = torch.max(outputs, 1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_metadata.extend(metadata)
    
    results = {
        'predictions': np.array(all_preds),
        'labels': np.array(all_labels),
        'metadata': all_metadata
    }
    
    if return_probs:
        results['probabilities'] = np.array(all_probs)
    
    return results


def calculate_metrics(results: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate evaluation metrics from test results.
    
    Args:
        results: Test results dictionary
    
    Returns:
        Dict with metrics
    """
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix
    )
    
    y_true = results['labels']
    y_pred = results['predictions']
    
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, average='binary', zero_division=0),
        'recall': recall_score(y_true, y_pred, average='binary', zero_division=0),
        'f1': f1_score(y_true, y_pred, average='binary', zero_division=0)
    }
    
    # ROC-AUC if probabilities available
    if 'probabilities' in results:
        try:
            metrics['roc_auc'] = roc_auc_score(y_true, results['probabilities'][:, 1])
        except:
            metrics['roc_auc'] = 0.0
    
    # Confusion matrix
    metrics['confusion_matrix'] = confusion_matrix(y_true, y_pred).tolist()
    
    return metrics


def save_predictions(results: Dict[str, Any], output_path: str):
    """
    Save predictions to JSON file.
    
    Args:
        results: Test results dictionary
        output_path: Path to save predictions
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy arrays to lists for JSON serialization
    save_data = {
        'predictions': results['predictions'].tolist(),
        'labels': results['labels'].tolist(),
        'metadata': results['metadata']
    }
    
    if 'probabilities' in results:
        save_data['probabilities'] = results['probabilities'].tolist()
    
    with open(output_path, 'w') as f:
        json.dump(save_data, f, indent=2)
    
    print(f"[Test] Saved predictions to {output_path}")


def save_metrics(metrics: Dict[str, float], output_path: str):
    """
    Save metrics to JSON file.
    
    Args:
        metrics: Metrics dictionary
        output_path: Path to save metrics
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"[Test] Saved metrics to {output_path}")


def print_metrics(metrics: Dict[str, float]):
    """
    Print metrics in readable format.
    
    Args:
        metrics: Metrics dictionary
    """
    print("\n" + "=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    
    print(f"\nOverall Metrics:")
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  F1 Score:  {metrics['f1']:.4f}")
    
    if 'roc_auc' in metrics:
        print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
    
    print(f"\nConfusion Matrix:")
    cm = np.array(metrics['confusion_matrix'])
    print(f"  True Negatives (Real correctly identified): {cm[0, 0]}")
    print(f"  False Positives (Real misidentified as AI): {cm[0, 1]}")
    print(f"  False Negatives (AI misidentified as Real): {cm[1, 0]}")
    print(f"  True Positives (AI correctly identified):    {cm[1, 1]}")
    
    print("\n" + "=" * 80)


def test(config: Dict[str, Any]):
    """
    Main test function.
    
    Args:
        config: Test configuration dictionary
    """
    # Get device
    device = get_device()
    
    # Create model
    print(f"\n[Test] Creating model: {config['model']['architecture']}")
    model = create_model(
        architecture=config['model']['architecture'],
        num_classes=config['model']['num_classes'],
        pretrained=False  # Load from checkpoint
    )
    model = model.to(device)
    
    # Load checkpoint
    checkpoint_path = config['test'].get('checkpoint_path')
    if not checkpoint_path:
        raise ValueError("checkpoint_path must be specified in config")
    
    print(f"[Test] Loading checkpoint from {checkpoint_path}")
    checkpoint_manager = CheckpointManager(
        checkpoint_dir=str(Path(checkpoint_path).parent)
    )
    checkpoint_manager.load(model, checkpoint_path=checkpoint_path)
    
    # Create test dataset
    print(f"\n[Test] Creating test dataset...")
    _, test_transform = get_default_transforms(
        image_size=config['data']['image_size'],
        augment=False
    )
    
    test_dataset = TruthLensDataset(
        metadata_path=config['data']['test_metadata'],
        dataset_dir=config['data']['dataset_dir'],
        split='val',  # Using val as test for now
        transform=test_transform
    )
    
    print(f"[Test] Test dataset size: {len(test_dataset)}")
    
    # Create test data loader
    test_loader = DataLoader(
        test_dataset,
        batch_size=config['data']['batch_size'],
        shuffle=False,
        num_workers=config['data'].get('num_workers', 4),
        pin_memory=config['data'].get('pin_memory', True)
    )
    
    print(f"[Test] Test batches: {len(test_loader)}")
    
    # Test model
    print(f"\n[Test] Running inference...")
    results = test_model(
        model=model,
        test_loader=test_loader,
        device=device,
        return_probs=config['test'].get('return_probs', True)
    )
    
    # Calculate metrics
    metrics = calculate_metrics(results)
    
    # Print metrics
    print_metrics(metrics)
    
    # Save predictions
    if config['test'].get('save_predictions', True):
        predictions_path = config['test'].get('predictions_output', 'test_predictions.json')
        save_predictions(results, predictions_path)
    
    # Save metrics
    if config['test'].get('save_metrics', True):
        metrics_path = config['test'].get('metrics_output', 'test_metrics.json')
        save_metrics(metrics, metrics_path)
    
    return results, metrics


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load test configuration from YAML file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Test TruthLens AI detection model')
    parser.add_argument('--config', type=str, required=True, help='Path to test config file')
    parser.add_argument('--checkpoint', type=str, help='Path to model checkpoint (overrides config)')
    parser.add_argument('--output', type=str, help='Path to save results (overrides config)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override checkpoint if specified
    if args.checkpoint:
        config['test']['checkpoint_path'] = args.checkpoint
    
    # Override output if specified
    if args.output:
        config['test']['predictions_output'] = args.output
    
    # Run test
    test(config)


if __name__ == '__main__':
    main()

"""
Comprehensive Evaluation Script
===============================
Evaluate trained models with full metrics, error analysis, and benchmarking.
"""

import argparse
import yaml
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from pathlib import Path
from typing import Dict, Any
import numpy as np
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.dataset import TruthLensDataset
from app.training.dataloader import get_default_transforms
from app.training.models import create_model
from app.training.utils import get_device, CheckpointManager
from app.training.validate import validate_model, print_metrics, save_metrics
from app.training.error_analysis import analyze_errors
from app.training.benchmarking import benchmark_model
from app.training.plotting import (
    plot_roc_curve, plot_pr_curve, plot_confusion_matrix,
    plot_per_generator_metrics, plot_per_dataset_metrics
)


def comprehensive_evaluate(config: Dict[str, Any]):
    """
    Run comprehensive model evaluation.
    
    Args:
        config: Evaluation configuration dictionary
    """
    # Get device
    device = get_device()
    
    # Create model
    print(f"\n[Evaluate] Creating model: {config['model']['architecture']}")
    model = create_model(
        architecture=config['model']['architecture'],
        num_classes=config['model']['num_classes'],
        pretrained=False  # Load from checkpoint
    )
    model = model.to(device)
    
    # Load checkpoint
    checkpoint_path = config['evaluation'].get('checkpoint_path')
    if not checkpoint_path:
        raise ValueError("checkpoint_path must be specified in config")
    
    print(f"[Evaluate] Loading checkpoint from {checkpoint_path}")
    checkpoint_manager = CheckpointManager(
        checkpoint_dir=str(Path(checkpoint_path).parent)
    )
    checkpoint_manager.load(model, checkpoint_path=checkpoint_path)
    
    # Create validation dataset
    print(f"\n[Evaluate] Creating validation dataset...")
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
    val_loader = DataLoader(
        val_dataset,
        batch_size=config['data']['batch_size'],
        shuffle=False,
        num_workers=config['data'].get('num_workers', 4),
        pin_memory=config['data'].get('pin_memory', True)
    )
    
    print(f"[Evaluate] Validation dataset size: {len(val_dataset)}")
    print(f"[Evaluate] Validation batches: {len(val_loader)}")
    
    # Create loss function
    criterion = nn.CrossEntropyLoss()
    
    # Validate model
    print(f"\n[Evaluate] Running validation...")
    results = validate_model(model, val_loader, device, criterion)
    
    # Print metrics
    print_metrics(results)
    
    # Create output directory
    output_dir = Path(config['evaluation'].get('output_dir', 'evaluation_results'))
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save metrics
    metrics_path = output_dir / 'metrics.json'
    save_metrics(results, metrics_path)
    
    # Error analysis
    if config['evaluation'].get('error_analysis', True):
        print(f"\n[Evaluate] Running error analysis...")
        error_analysis_results = analyze_errors(
            predictions=np.array(results['predictions']),
            labels=np.array(results['labels']),
            probabilities=np.array(results['probabilities']),
            metadata=results['metadata'],
            save_dir=output_dir
        )
        results['error_analysis'] = error_analysis_results
    
    # Benchmarking
    if config['evaluation'].get('benchmark', True):
        print(f"\n[Evaluate] Running benchmarking...")
        benchmark_results = benchmark_model(
            model=model,
            device=device,
            dataloader=val_loader,
            checkpoint_path=checkpoint_path,
            save_dir=output_dir
        )
        results['benchmark'] = benchmark_results
    
    # Generate plots
    if config['evaluation'].get('plots', True):
        print(f"\n[Evaluate] Generating plots...")
        plots_dir = output_dir / 'plots'
        plots_dir.mkdir(parents=True, exist_ok=True)
        
        # ROC curve
        if 'probabilities' in results:
            y_true = np.array(results['labels'])
            y_scores = np.array(results['probabilities'])[:, 1]
            plot_roc_curve(y_true, y_scores, plots_dir / 'roc_curve.png')
        
        # PR curve
        if 'probabilities' in results:
            y_true = np.array(results['labels'])
            y_scores = np.array(results['probabilities'])[:, 1]
            plot_pr_curve(y_true, y_scores, plots_dir / 'pr_curve.png')
        
        # Confusion matrix
        if 'confusion_matrix' in results:
            cm = np.array(results['confusion_matrix'])
            plot_confusion_matrix(cm, plots_dir / 'confusion_matrix.png')
        
        # Per-generator metrics
        if 'generator_metrics' in results:
            plot_per_generator_metrics(
                results['generator_metrics'],
                plots_dir / 'per_generator_metrics.png'
            )
        
        # Per-dataset metrics
        if 'dataset_metrics' in results:
            plot_per_dataset_metrics(
                results['dataset_metrics'],
                plots_dir / 'per_dataset_metrics.png'
            )
    
    # Save complete results
    complete_results_path = output_dir / 'complete_results.json'
    with open(complete_results_path, 'w') as f:
        # Convert numpy arrays to lists for JSON serialization
        save_results = {
            'metrics': {
                'accuracy': results['accuracy'],
                'precision': results['precision'],
                'recall': results['recall'],
                'f1': results['f1'],
                'roc_auc': results['roc_auc'],
                'pr_auc': results['pr_auc'],
                'confusion_matrix': results['confusion_matrix'],
                'num_samples': results['num_samples']
            },
            'generator_metrics': results.get('generator_metrics', {}),
            'dataset_metrics': results.get('dataset_metrics', {}),
            'error_analysis': results.get('error_analysis', {}),
            'benchmark': results.get('benchmark', {})
        }
        json.dump(save_results, f, indent=2)
    
    print(f"\n[Evaluate] Evaluation complete!")
    print(f"[Evaluate] Results saved to: {output_dir}")
    print(f"[Evaluate] Metrics: {metrics_path}")
    print(f"[Evaluate] Complete results: {complete_results_path}")
    
    return results


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load evaluation configuration from YAML file.
    
    Args:
        config_path: Path to config file
    
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Comprehensive evaluation of TruthLens model')
    parser.add_argument('--config', type=str, required=True, help='Path to evaluation config file')
    parser.add_argument('--checkpoint', type=str, help='Path to model checkpoint (overrides config)')
    parser.add_argument('--output', type=str, help='Output directory (overrides config)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override checkpoint if specified
    if args.checkpoint:
        config['evaluation']['checkpoint_path'] = args.checkpoint
    
    # Override output if specified
    if args.output:
        config['evaluation']['output_dir'] = args.output
    
    # Run evaluation
    comprehensive_evaluate(config)


if __name__ == '__main__':
    main()

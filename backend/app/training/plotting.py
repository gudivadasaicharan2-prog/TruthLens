"""
Training Visualization
======================
Generate training plots including loss curves, accuracy curves, ROC curves,
PR curves, and confusion matrices.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sklearn.metrics import roc_curve, auc, precision_recall_curve
import seaborn as sns


def plot_training_curves(
    history: Dict[str, List[float]],
    save_path: Path,
    title: str = "Training Curves"
):
    """
    Plot training and validation loss and accuracy curves.
    
    Args:
        history: Training history dictionary with 'train_loss', 'val_loss',
                 'train_accuracy', 'val_accuracy' keys
        save_path: Path to save the plot
        title: Plot title
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    epochs = range(1, len(history.get('train_loss', [])) + 1)
    
    # Loss curve
    if 'train_loss' in history:
        axes[0].plot(epochs, history['train_loss'], 'b-', label='Train Loss', linewidth=2)
    if 'val_loss' in history:
        axes[0].plot(epochs, history['val_loss'], 'r-', label='Val Loss', linewidth=2)
    
    axes[0].set_xlabel('Epoch', fontsize=12)
    axes[0].set_ylabel('Loss', fontsize=12)
    axes[0].set_title('Training and Validation Loss', fontsize=14)
    axes[0].legend(fontsize=10)
    axes[0].grid(True, alpha=0.3)
    
    # Accuracy curve
    if 'train_accuracy' in history:
        axes[1].plot(epochs, history['train_accuracy'], 'b-', label='Train Accuracy', linewidth=2)
    if 'val_accuracy' in history:
        axes[1].plot(epochs, history['val_accuracy'], 'r-', label='Val Accuracy', linewidth=2)
    
    axes[1].set_xlabel('Epoch', fontsize=12)
    axes[1].set_ylabel('Accuracy', fontsize=12)
    axes[1].set_title('Training and Validation Accuracy', fontsize=14)
    axes[1].legend(fontsize=10)
    axes[1].grid(True, alpha=0.3)
    
    plt.suptitle(title, fontsize=16, y=1.02)
    plt.tight_layout()
    
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[Plotting] Saved training curves to {save_path}")


def plot_roc_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    save_path: Path,
    title: str = "ROC Curve"
):
    """
    Plot ROC curve.
    
    Args:
        y_true: True labels
        y_scores: Predicted probabilities for positive class
        save_path: Path to save the plot
        title: Plot title
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_scores)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 8))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random classifier')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate', fontsize=12)
    plt.ylabel('True Positive Rate', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(loc="lower right", fontsize=10)
    plt.grid(True, alpha=0.3)
    
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[Plotting] Saved ROC curve to {save_path}")


def plot_pr_curve(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    save_path: Path,
    title: str = "Precision-Recall Curve"
):
    """
    Plot Precision-Recall curve.
    
    Args:
        y_true: True labels
        y_scores: Predicted probabilities for positive class
        save_path: Path to save the plot
        title: Plot title
    """
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
    pr_auc = auc(recall, precision)
    
    plt.figure(figsize=(8, 8))
    plt.plot(recall, precision, color='blue', lw=2, label=f'PR curve (AUC = {pr_auc:.4f})')
    plt.xlabel('Recall', fontsize=12)
    plt.ylabel('Precision', fontsize=12)
    plt.title(title, fontsize=14)
    plt.legend(loc="lower left", fontsize=10)
    plt.grid(True, alpha=0.3)
    
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[Plotting] Saved PR curve to {save_path}")


def plot_confusion_matrix(
    cm: np.ndarray,
    save_path: Path,
    class_names: Optional[List[str]] = None,
    title: str = "Confusion Matrix"
):
    """
    Plot confusion matrix.
    
    Args:
        cm: Confusion matrix
        save_path: Path to save the plot
        class_names: Optional list of class names
        title: Plot title
    """
    if class_names is None:
        class_names = ['Real', 'AI']
    
    plt.figure(figsize=(8, 6))
    
    # Normalize confusion matrix
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    
    # Plot using seaborn heatmap
    sns.heatmap(
        cm_normalized,
        annot=True,
        fmt='.2f',
        cmap='Blues',
        xticklabels=class_names,
        yticklabels=class_names,
        cbar_kws={'label': 'Normalized Count'}
    )
    
    plt.xlabel('Predicted Label', fontsize=12)
    plt.ylabel('True Label', fontsize=12)
    plt.title(title, fontsize=14)
    
    # Add raw counts in parentheses
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(
                j + 0.5,
                i + 0.7,
                f'({cm[i, j]})',
                ha='center',
                va='center',
                fontsize=8,
                color='gray'
            )
    
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[Plotting] Saved confusion matrix to {save_path}")


def plot_per_generator_metrics(
    generator_metrics: Dict[str, Dict[str, float]],
    save_path: Path,
    title: str = "Per-Generator Metrics"
):
    """
    Plot per-generator metrics bar chart.
    
    Args:
        generator_metrics: Dictionary mapping generator to metrics
        save_path: Path to save the plot
        title: Plot title
    """
    if not generator_metrics:
        print("[Plotting] No generator metrics to plot")
        return
    
    generators = list(generator_metrics.keys())
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, metric in enumerate(metrics):
        values = [generator_metrics[gen].get(metric, 0) for gen in generators]
        
        axes[idx].bar(generators, values, color='steelblue', alpha=0.7)
        axes[idx].set_xlabel('Generator', fontsize=10)
        axes[idx].set_ylabel(metric.capitalize(), fontsize=10)
        axes[idx].set_title(f'{metric.capitalize()} per Generator', fontsize=12)
        axes[idx].set_ylim([0, 1])
        axes[idx].grid(True, alpha=0.3, axis='y')
        axes[idx].tick_params(axis='x', rotation=45)
    
    plt.suptitle(title, fontsize=16, y=1.02)
    plt.tight_layout()
    
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[Plotting] Saved per-generator metrics to {save_path}")


def plot_per_dataset_metrics(
    dataset_metrics: Dict[str, Dict[str, float]],
    save_path: Path,
    title: str = "Per-Dataset Metrics"
):
    """
    Plot per-dataset metrics bar chart.
    
    Args:
        dataset_metrics: Dictionary mapping dataset to metrics
        save_path: Path to save the plot
        title: Plot title
    """
    if not dataset_metrics:
        print("[Plotting] No dataset metrics to plot")
        return
    
    datasets = list(dataset_metrics.keys())
    metrics = ['accuracy', 'precision', 'recall', 'f1']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    for idx, metric in enumerate(metrics):
        values = [dataset_metrics[ds].get(metric, 0) for ds in datasets]
        
        axes[idx].bar(datasets, values, color='coral', alpha=0.7)
        axes[idx].set_xlabel('Dataset', fontsize=10)
        axes[idx].set_ylabel(metric.capitalize(), fontsize=10)
        axes[idx].set_title(f'{metric.capitalize()} per Dataset', fontsize=12)
        axes[idx].set_ylim([0, 1])
        axes[idx].grid(True, alpha=0.3, axis='y')
        axes[idx].tick_params(axis='x', rotation=45)
    
    plt.suptitle(title, fontsize=16, y=1.02)
    plt.tight_layout()
    
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"[Plotting] Saved per-dataset metrics to {save_path}")


def generate_all_plots(
    history: Dict[str, List[float]],
    validation_results: Dict[str, any],
    plots_dir: Path
):
    """
    Generate all training plots.
    
    Args:
        history: Training history dictionary
        validation_results: Validation results dictionary
        plots_dir: Directory to save plots
    """
    plots_dir = Path(plots_dir)
    plots_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[Plotting] Generating all plots in {plots_dir}")
    
    # Training curves
    plot_training_curves(
        history,
        plots_dir / "training_curves.png",
        title="Training and Validation Curves"
    )
    
    # ROC curve
    if 'probabilities' in validation_results and 'labels' in validation_results:
        y_true = np.array(validation_results['labels'])
        y_scores = np.array(validation_results['probabilities'])[:, 1]  # AI class probability
        plot_roc_curve(
            y_true, y_scores,
            plots_dir / "roc_curve.png",
            title="ROC Curve"
        )
    
    # PR curve
    if 'probabilities' in validation_results and 'labels' in validation_results:
        y_true = np.array(validation_results['labels'])
        y_scores = np.array(validation_results['probabilities'])[:, 1]  # AI class probability
        plot_pr_curve(
            y_true, y_scores,
            plots_dir / "pr_curve.png",
            title="Precision-Recall Curve"
        )
    
    # Confusion matrix
    if 'confusion_matrix' in validation_results:
        cm = np.array(validation_results['confusion_matrix'])
        plot_confusion_matrix(
            cm,
            plots_dir / "confusion_matrix.png",
            title="Confusion Matrix"
        )
    
    # Per-generator metrics
    if 'generator_metrics' in validation_results:
        plot_per_generator_metrics(
            validation_results['generator_metrics'],
            plots_dir / "per_generator_metrics.png",
            title="Per-Generator Metrics"
        )
    
    # Per-dataset metrics
    if 'dataset_metrics' in validation_results:
        plot_per_dataset_metrics(
            validation_results['dataset_metrics'],
            plots_dir / "per_dataset_metrics.png",
            title="Per-Dataset Metrics"
        )
    
    print(f"[Plotting] All plots generated successfully")

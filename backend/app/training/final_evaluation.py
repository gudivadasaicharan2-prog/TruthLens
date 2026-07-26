"""
Final Evaluation Pipeline for TruthLens Model
============================================
Comprehensive evaluation of trained model on validation dataset.
"""

import sys
from pathlib import Path
import json
import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, precision_recall_curve
)
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.dataset import TruthLensDataset
from app.training.dataloader import create_data_loaders, get_default_transforms
from app.training.models import create_model
from app.training.utils import get_device


def load_checkpoint(checkpoint_path: str, model: nn.Module, device: torch.device):
    """
    Load model from checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint file
        model: Model to load weights into
        device: Device to load model on
    
    Returns:
        Checkpoint dictionary
    """
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    print(f"[Evaluation] Loaded checkpoint from {checkpoint_path}")
    print(f"  Epoch: {checkpoint['epoch']}")
    print(f"  Score: {checkpoint['score']:.4f}")
    return checkpoint


def evaluate_model(model: nn.Module, data_loader, device: torch.device):
    """
    Evaluate model on dataset.
    
    Args:
        model: Model to evaluate
        data_loader: DataLoader for evaluation
        device: Device to run evaluation on
    
    Returns:
        Dict with predictions, labels, and probabilities
    """
    model.eval()
    
    all_predictions = []
    all_labels = []
    all_probabilities = []
    
    with torch.no_grad():
        for images, labels, _ in tqdm(data_loader, desc="Evaluating"):
            images = images.to(device)
            labels = labels.to(device)
            
            outputs = model(images)
            probabilities = torch.softmax(outputs, dim=1)
            predictions = torch.argmax(outputs, dim=1)
            
            all_predictions.extend(predictions.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probabilities.extend(probabilities.cpu().numpy())
    
    return {
        'predictions': np.array(all_predictions),
        'labels': np.array(all_labels),
        'probabilities': np.array(all_probabilities)
    }


def calculate_metrics(labels: np.ndarray, predictions: np.ndarray, probabilities: np.ndarray):
    """
    Calculate comprehensive evaluation metrics.
    
    Args:
        labels: Ground truth labels
        predictions: Model predictions
        probabilities: Model output probabilities
    
    Returns:
        Dict with all metrics
    """
    metrics = {}
    
    # Basic metrics
    metrics['accuracy'] = accuracy_score(labels, predictions)
    metrics['precision'] = precision_score(labels, predictions, average='binary')
    metrics['recall'] = recall_score(labels, predictions, average='binary')
    metrics['f1_score'] = f1_score(labels, predictions, average='binary')
    
    # ROC AUC (use probability of positive class)
    if probabilities.shape[1] >= 2:
        metrics['roc_auc'] = roc_auc_score(labels, probabilities[:, 1])
    else:
        metrics['roc_auc'] = 0.0
    
    # Confusion matrix
    metrics['confusion_matrix'] = confusion_matrix(labels, predictions).tolist()
    
    # Classification report
    metrics['classification_report'] = classification_report(
        labels, predictions, 
        target_names=['Real', 'AI'],
        output_dict=True
    )
    
    return metrics


def plot_confusion_matrix(cm: np.ndarray, save_path: str):
    """
    Plot and save confusion matrix.
    
    Args:
        cm: Confusion matrix
        save_path: Path to save plot
    """
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Real', 'AI'], 
                yticklabels=['Real', 'AI'])
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Evaluation] Saved confusion matrix to {save_path}")


def plot_roc_curve(labels: np.ndarray, probabilities: np.ndarray, save_path: str):
    """
    Plot and save ROC curve.
    
    Args:
        labels: Ground truth labels
        probabilities: Model output probabilities
        save_path: Path to save plot
    """
    if probabilities.shape[1] < 2:
        print("[Evaluation] Skipping ROC curve (insufficient probability dimensions)")
        return
    
    fpr, tpr, _ = roc_curve(labels, probabilities[:, 1])
    auc_score = roc_auc_score(labels, probabilities[:, 1])
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc_score:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Evaluation] Saved ROC curve to {save_path}")


def plot_precision_recall_curve(labels: np.ndarray, probabilities: np.ndarray, save_path: str):
    """
    Plot and save precision-recall curve.
    
    Args:
        labels: Ground truth labels
        probabilities: Model output probabilities
        save_path: Path to save plot
    """
    if probabilities.shape[1] < 2:
        print("[Evaluation] Skipping Precision-Recall curve (insufficient probability dimensions)")
        return
    
    precision, recall, _ = precision_recall_curve(labels, probabilities[:, 1])
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='blue', lw=2)
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[Evaluation] Saved Precision-Recall curve to {save_path}")


def save_classification_report(metrics: dict, save_path: str):
    """
    Save classification report to text file.
    
    Args:
        metrics: Metrics dictionary
        save_path: Path to save report
    """
    with open(save_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("TruthLens Model Evaluation Report\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Overall Metrics:\n")
        f.write("-" * 40 + "\n")
        f.write(f"Accuracy:  {metrics['accuracy']:.4f}\n")
        f.write(f"Precision: {metrics['precision']:.4f}\n")
        f.write(f"Recall:    {metrics['recall']:.4f}\n")
        f.write(f"F1 Score:  {metrics['f1_score']:.4f}\n")
        f.write(f"ROC AUC:   {metrics['roc_auc']:.4f}\n\n")
        
        f.write("Classification Report:\n")
        f.write("-" * 40 + "\n")
        report = metrics['classification_report']
        for class_name in ['Real', 'AI']:
            if class_name in report:
                class_metrics = report[class_name]
                f.write(f"\n{class_name.upper()}:\n")
                f.write(f"  Precision: {class_metrics['precision']:.4f}\n")
                f.write(f"  Recall:    {class_metrics['recall']:.4f}\n")
                f.write(f"  F1-Score:  {class_metrics['f1-score']:.4f}\n")
                f.write(f"  Support:   {class_metrics['support']}\n")
        
        if 'macro avg' in report:
            f.write(f"\nMACRO AVERAGE:\n")
            f.write(f"  Precision: {report['macro avg']['precision']:.4f}\n")
            f.write(f"  Recall:    {report['macro avg']['recall']:.4f}\n")
            f.write(f"  F1-Score:  {report['macro avg']['f1-score']:.4f}\n")
        
        if 'weighted avg' in report:
            f.write(f"\nWEIGHTED AVERAGE:\n")
            f.write(f"  Precision: {report['weighted avg']['precision']:.4f}\n")
            f.write(f"  Recall:    {report['weighted avg']['recall']:.4f}\n")
            f.write(f"  F1-Score:  {report['weighted avg']['f1-score']:.4f}\n")
        
        f.write("\n" + "=" * 80 + "\n")
    
    print(f"[Evaluation] Saved classification report to {save_path}")


def save_metrics_json(metrics: dict, save_path: str):
    """
    Save metrics to JSON file.
    
    Args:
        metrics: Metrics dictionary
        save_path: Path to save JSON
    """
    with open(save_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"[Evaluation] Saved metrics JSON to {save_path}")


def print_summary(metrics: dict):
    """
    Print clean summary to console.
    
    Args:
        metrics: Metrics dictionary
    """
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
    print("=" * 80)
    
    # Print confusion matrix
    cm = np.array(metrics['confusion_matrix'])
    print("\nConfusion Matrix:")
    print("              Predicted")
    print("              Real    AI")
    print(f"Actual Real   {cm[0,0]:4d}  {cm[0,1]:4d}")
    print(f"Actual AI     {cm[1,0]:4d}  {cm[1,1]:4d}")
    print("=" * 80)


def main():
    """Main evaluation pipeline."""
    
    # Paths
    checkpoint_path = "experiments/cifake_efficientnet_b4_baseline/checkpoints/latest_checkpoint.pth"
    metadata_path = "TruthLensDataset/metadata.csv"
    dataset_dir = "TruthLensDataset"
    output_dir = "experiments/cifake_efficientnet_b4_baseline/evaluation"
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("TruthLens Model Evaluation Pipeline")
    print("=" * 80)
    
    # Get device
    device = get_device()
    
    # Load model
    print("\n[Step 1] Loading model...")
    model = create_model(
        architecture='efficientnet_b4',
        num_classes=2,
        pretrained=False,
        dropout=0.3
    )
    
    # Load checkpoint
    checkpoint = load_checkpoint(checkpoint_path, model, device)
    
    # Create validation dataset
    print("\n[Step 2] Loading validation dataset...")
    _, val_transform = get_default_transforms(image_size=224, augment=False)
    
    val_dataset = TruthLensDataset(
        metadata_path=metadata_path,
        dataset_dir=dataset_dir,
        split='val',
        transform=val_transform
    )
    
    print(f"Validation samples: {len(val_dataset)}")
    
    # Create validation dataloader
    val_loader = torch.utils.data.DataLoader(
        val_dataset,
        batch_size=32,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )
    
    # Evaluate model
    print("\n[Step 3] Running evaluation...")
    results = evaluate_model(model, val_loader, device)
    
    # Calculate metrics
    print("\n[Step 4] Calculating metrics...")
    metrics = calculate_metrics(
        results['labels'],
        results['predictions'],
        results['probabilities']
    )
    
    # Generate visualizations
    print("\n[Step 5] Generating visualizations...")
    plot_confusion_matrix(
        np.array(metrics['confusion_matrix']),
        str(output_path / 'confusion_matrix.png')
    )
    plot_roc_curve(
        results['labels'],
        results['probabilities'],
        str(output_path / 'roc_curve.png')
    )
    plot_precision_recall_curve(
        results['labels'],
        results['probabilities'],
        str(output_path / 'precision_recall_curve.png')
    )
    
    # Save outputs
    print("\n[Step 6] Saving outputs...")
    save_classification_report(
        metrics,
        str(output_path / 'classification_report.txt')
    )
    save_metrics_json(
        metrics,
        str(output_path / 'metrics.json')
    )
    
    # Print summary
    print("\n[Step 7] Final summary...")
    print_summary(metrics)
    
    print(f"\n[Evaluation] Complete! Results saved to: {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()

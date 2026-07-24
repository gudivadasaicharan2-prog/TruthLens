"""
AI Image Detection Validator
=============================
Validation and evaluation utilities for the trained model.
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from typing import Dict, Tuple, Optional
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix


class AIDetectionValidator:
    """
    Validator for AI image detection model.
    """
    
    def __init__(
        self,
        model: nn.Module,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        Initialize validator.
        
        Args:
            model: The model to validate
            device: Device to run validation on
        """
        self.model = model.to(device)
        self.device = device
        self.model.eval()
    
    def evaluate(
        self,
        dataloader: DataLoader,
        threshold: float = 0.5
    ) -> Dict:
        """
        Evaluate model on a dataset.
        
        Args:
            dataloader: Data loader for evaluation
            threshold: Classification threshold
            
        Returns:
            Dictionary with evaluation metrics
        """
        all_predictions = []
        all_labels = []
        all_probabilities = []
        total_loss = 0.0
        
        criterion = nn.BCEWithLogitsLoss()
        
        with torch.no_grad():
            for images, labels in dataloader:
                images = images.to(self.device)
                labels = labels.float().to(self.device)
                
                # Forward pass
                outputs = self.model(images)
                loss = criterion(outputs.squeeze(), labels)
                
                # Get probabilities
                probabilities = torch.sigmoid(outputs.squeeze())
                predictions = (probabilities > threshold).float()
                
                # Collect results
                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_probabilities.extend(probabilities.cpu().numpy())
                
                total_loss += loss.item()
        
        # Convert to numpy arrays
        all_predictions = np.array(all_predictions)
        all_labels = np.array(all_labels)
        all_probabilities = np.array(all_probabilities)
        
        # Calculate metrics
        accuracy = accuracy_score(all_labels, all_predictions)
        precision = precision_score(all_labels, all_predictions, zero_division=0)
        recall = recall_score(all_labels, all_predictions, zero_division=0)
        f1 = f1_score(all_labels, all_predictions, zero_division=0)
        
        # AUC-ROC
        try:
            auc = roc_auc_score(all_labels, all_probabilities)
        except:
            auc = 0.0
        
        # Confusion matrix
        cm = confusion_matrix(all_labels, all_predictions)
        
        # Average loss
        avg_loss = total_loss / len(dataloader)
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'auc_roc': auc,
            'confusion_matrix': cm.tolist(),
            'loss': avg_loss,
            'threshold': threshold,
            'num_samples': len(all_labels)
        }
        
        return metrics
    
    def print_metrics(self, metrics: Dict):
        """
        Print evaluation metrics in a readable format.
        
        Args:
            metrics: Dictionary of metrics from evaluate()
        """
        print("=" * 60)
        print("Evaluation Results")
        print("=" * 60)
        print(f"Accuracy:  {metrics['accuracy']:.4f}")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall:    {metrics['recall']:.4f}")
        print(f"F1 Score:  {metrics['f1_score']:.4f}")
        print(f"AUC-ROC:   {metrics['auc_roc']:.4f}")
        print(f"Loss:      {metrics['loss']:.4f}")
        print(f"Samples:   {metrics['num_samples']}")
        print()
        print("Confusion Matrix:")
        cm = metrics['confusion_matrix']
        print(f"  TN={cm[0][0]:4d}  FP={cm[0][1]:4d}")
        print(f"  FN={cm[1][0]:4d}  TP={cm[1][1]:4d}")
        print("=" * 60)
    
    def predict_batch(
        self,
        images: torch.Tensor,
        threshold: float = 0.5
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Predict on a batch of images.
        
        Args:
            images: Batch of images (B, C, H, W)
            threshold: Classification threshold
            
        Returns:
            Tuple of (predictions, probabilities)
        """
        images = images.to(self.device)
        
        with torch.no_grad():
            outputs = self.model(images)
            probabilities = torch.sigmoid(outputs.squeeze())
            predictions = (probabilities > threshold).float()
        
        return predictions, probabilities


def compare_models(
    model1: nn.Module,
    model2: nn.Module,
    dataloader: DataLoader,
    model1_name: str = "Model 1",
    model2_name: str = "Model 2",
    device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
) -> Dict:
    """
    Compare two models on the same dataset.
    
    Args:
        model1: First model
        model2: Second model
        dataloader: Data loader for evaluation
        model1_name: Name for first model
        model2_name: Name for second model
        device: Device to run on
        
    Returns:
        Dictionary with comparison results
    """
    validator1 = AIDetectionValidator(model1, device)
    validator2 = AIDetectionValidator(model2, device)
    
    metrics1 = validator1.evaluate(dataloader)
    metrics2 = validator2.evaluate(dataloader)
    
    comparison = {
        model1_name: metrics1,
        model2_name: metrics2,
        'improvement': {
            'accuracy': metrics2['accuracy'] - metrics1['accuracy'],
            'f1_score': metrics2['f1_score'] - metrics1['f1_score'],
            'auc_roc': metrics2['auc_roc'] - metrics1['auc_roc']
        }
    }
    
    print(f"\nComparison: {model1_name} vs {model2_name}")
    print(f"Accuracy improvement: {comparison['improvement']['accuracy']:+.4f}")
    print(f"F1 Score improvement:  {comparison['improvement']['f1_score']:+.4f}")
    print(f"AUC-ROC improvement:   {comparison['improvement']['auc_roc']:+.4f}")
    
    return comparison

"""
Unit Test for Custom Metrics Implementation
===========================================
Tests NumPy-only metrics against scikit-learn when available.
"""

import sys
from pathlib import Path
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.benchmark.benchmark import BenchmarkManager


def test_metrics():
    """
    Test custom metrics implementation against known values and sklearn (if available).
    """
    print("=" * 80)
    print("Testing Custom Metrics Implementation")
    print("=" * 80)
    
    # Hard-coded test data (20 samples)
    # Labels: 0 = Real, 1 = AI
    labels = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 1])
    
    # Predictions
    predictions = np.array([0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1])
    
    # Probabilities for positive class (AI)
    probabilities = np.array([
        [0.9, 0.1],  # Correct: Real
        [0.8, 0.2],  # Correct: Real
        [0.7, 0.3],  # Correct: Real
        [0.4, 0.6],  # Incorrect: Real predicted as AI
        [0.95, 0.05], # Correct: Real
        [0.2, 0.8],  # Correct: AI
        [0.1, 0.9],  # Correct: AI
        [0.3, 0.7],  # Correct: AI
        [0.6, 0.4],  # Incorrect: AI predicted as Real
        [0.15, 0.85], # Correct: AI
        [0.85, 0.15], # Correct: Real
        [0.45, 0.55], # Incorrect: Real predicted as AI
        [0.25, 0.75], # Correct: AI
        [0.2, 0.8],   # Correct: AI
        [0.9, 0.1],   # Correct: Real
        [0.1, 0.9],   # Correct: AI
        [0.8, 0.2],   # Correct: Real
        [0.55, 0.45], # Incorrect: AI predicted as Real
        [0.75, 0.25], # Correct: Real
        [0.1, 0.9]    # Correct: AI
    ])
    
    # Create a minimal BenchmarkManager instance to access metric methods
    manager = BenchmarkManager(
        checkpoint_path="dummy.pth",
        output_dir="dummy_output",
        cache_dir="dummy_cache"
    )
    
    # Compute metrics using custom implementation
    results = {
        'predictions': predictions,
        'labels': labels,
        'probabilities': probabilities
    }
    
    custom_metrics = manager._calculate_metrics(results)
    
    print("\nCustom Implementation Results:")
    print("-" * 40)
    print(f"Accuracy:  {custom_metrics['accuracy']:.4f}")
    print(f"Precision: {custom_metrics['precision']:.4f}")
    print(f"Recall:    {custom_metrics['recall']:.4f}")
    print(f"F1 Score:  {custom_metrics['f1_score']:.4f}")
    print(f"ROC AUC:   {custom_metrics['roc_auc']:.4f}")
    print(f"Confusion Matrix:")
    cm = np.array(custom_metrics['confusion_matrix'])
    print(f"  {cm}")
    
    # Calculate expected values manually
    # From the data:
    # True Real: 10, True AI: 10
    # Predicted Real: 10, Predicted AI: 10
    # TN (Real correctly predicted as Real): 8
    # FP (Real incorrectly predicted as AI): 2
    # FN (AI incorrectly predicted as Real): 2
    # TP (AI correctly predicted as AI): 8
    
    expected_cm = np.array([[8, 2], [2, 8]])
    expected_accuracy = (8 + 8) / 20  # 16/20 = 0.8
    expected_precision = 8 / (8 + 2)  # 8/10 = 0.8
    expected_recall = 8 / (8 + 2)  # 8/10 = 0.8
    expected_f1 = 2 * (0.8 * 0.8) / (0.8 + 0.8)  # 0.8
    
    print("\nExpected Values (Manual Calculation):")
    print("-" * 40)
    print(f"Accuracy:  {expected_accuracy:.4f}")
    print(f"Precision: {expected_precision:.4f}")
    print(f"Recall:    {expected_recall:.4f}")
    print(f"F1 Score:  {expected_f1:.4f}")
    print(f"Confusion Matrix:")
    print(f"  {expected_cm}")
    
    # Verify against expected values
    print("\nVerification Against Expected Values:")
    print("-" * 40)
    
    tolerance = 1e-6
    
    accuracy_match = abs(custom_metrics['accuracy'] - expected_accuracy) < tolerance
    precision_match = abs(custom_metrics['precision'] - expected_precision) < tolerance
    recall_match = abs(custom_metrics['recall'] - expected_recall) < tolerance
    f1_match = abs(custom_metrics['f1_score'] - expected_f1) < tolerance
    cm_match = np.array_equal(cm, expected_cm)
    
    print(f"Accuracy:  {'PASS' if accuracy_match else 'FAIL'}")
    print(f"Precision: {'PASS' if precision_match else 'FAIL'}")
    print(f"Recall:    {'PASS' if recall_match else 'FAIL'}")
    print(f"F1 Score:  {'PASS' if f1_match else 'FAIL'}")
    print(f"Confusion Matrix: {'PASS' if cm_match else 'FAIL'}")
    
    # Compare with sklearn if available
    try:
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, f1_score,
            roc_auc_score, confusion_matrix
        )
        
        print("\nComparison with scikit-learn:")
        print("-" * 40)
        
        sklearn_accuracy = accuracy_score(labels, predictions)
        sklearn_precision = precision_score(labels, predictions, average='binary', zero_division=0)
        sklearn_recall = recall_score(labels, predictions, average='binary', zero_division=0)
        sklearn_f1 = f1_score(labels, predictions, average='binary', zero_division=0)
        sklearn_cm = confusion_matrix(labels, predictions)
        sklearn_roc_auc = roc_auc_score(labels, probabilities[:, 1])
        
        print(f"sklearn Accuracy:  {sklearn_accuracy:.4f}")
        print(f"sklearn Precision: {sklearn_precision:.4f}")
        print(f"sklearn Recall:    {sklearn_recall:.4f}")
        print(f"sklearn F1 Score:  {sklearn_f1:.4f}")
        print(f"sklearn ROC AUC:   {sklearn_roc_auc:.4f}")
        print(f"sklearn Confusion Matrix:")
        print(f"  {sklearn_cm}")
        
        # Compare
        sklearn_accuracy_match = abs(custom_metrics['accuracy'] - sklearn_accuracy) < tolerance
        sklearn_precision_match = abs(custom_metrics['precision'] - sklearn_precision) < tolerance
        sklearn_recall_match = abs(custom_metrics['recall'] - sklearn_recall) < tolerance
        sklearn_f1_match = abs(custom_metrics['f1_score'] - sklearn_f1) < tolerance
        sklearn_cm_match = np.array_equal(cm, sklearn_cm)
        sklearn_roc_auc_match = abs(custom_metrics['roc_auc'] - sklearn_roc_auc) < tolerance
        
        print("\nsklearn Comparison Results:")
        print("-" * 40)
        print(f"Accuracy:  {'PASS' if sklearn_accuracy_match else 'FAIL'}")
        print(f"Precision: {'PASS' if sklearn_precision_match else 'FAIL'}")
        print(f"Recall:    {'PASS' if sklearn_recall_match else 'FAIL'}")
        print(f"F1 Score:  {'PASS' if sklearn_f1_match else 'FAIL'}")
        print(f"ROC AUC:   {'PASS' if sklearn_roc_auc_match else 'FAIL'}")
        print(f"Confusion Matrix: {'PASS' if sklearn_cm_match else 'FAIL'}")
        
        all_pass = (accuracy_match and precision_match and recall_match and 
                    f1_match and cm_match and sklearn_accuracy_match and 
                    sklearn_precision_match and sklearn_recall_match and 
                    sklearn_f1_match and sklearn_cm_match and sklearn_roc_auc_match)
        
    except ImportError:
        print("\nsklearn not available - skipping comparison")
        all_pass = accuracy_match and precision_match and recall_match and f1_match and cm_match
    
    print("\n" + "=" * 80)
    if all_pass:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 80)
    
    return all_pass


if __name__ == "__main__":
    success = test_metrics()
    sys.exit(0 if success else 1)

"""
Run Evaluation Script
=====================
Script to run the evaluation framework on available images.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ai.evaluation import run_evaluation

if __name__ == "__main__":
    print("=" * 60)
    print("TruthLens Image Detection Evaluation")
    print("=" * 60)
    
    # Run evaluation
    predictions_csv, metrics = run_evaluation()
    
    print("\n" + "=" * 60)
    print("Evaluation Complete")
    print("=" * 60)
    
    if predictions_csv:
        print(f"\nPredictions saved to: {predictions_csv}")
    
    if metrics:
        print("\nMetrics:")
        for key, value in metrics.items():
            if key != 'confusion_matrix' and key != 'per_category_accuracy':
                print(f"  {key}: {value}")
        
        if 'per_category_accuracy' in metrics:
            print("\nPer-Category Accuracy:")
            for cat, acc in metrics['per_category_accuracy'].items():
                print(f"  {cat}: {acc:.4f}")

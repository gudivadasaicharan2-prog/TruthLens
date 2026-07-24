"""
Multi-threshold evaluation of trained classifier.
Tests different decision thresholds to find optimal F1 score.
"""

import csv
from pathlib import Path


def load_benchmark_results(csv_path: str = "benchmark_trained.csv"):
    """Load benchmark results from CSV."""
    results = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'filename': row['filename'],
                'ground_truth': row['ground_truth'],
                'prediction': row['prediction'],
                'confidence': float(row['confidence']),
                'ai_probability': float(row['ai_probability']),
                'forensic_score': float(row['forensic_score'])
            })
    return results


def compute_metrics_at_threshold(results, threshold: float):
    """
    Compute metrics at a specific AI probability threshold.
    
    Args:
        results: List of evaluation result dictionaries
        threshold: AI probability threshold for classification (decimal 0-1)
    
    Returns:
        Dictionary with metrics
    """
    # Convert predictions to binary based on threshold
    # Note: ai_probability in CSV is percentage (0-100), convert to decimal (0-1)
    def prediction_to_binary(ai_prob):
        ai_prob_decimal = ai_prob / 100.0  # Convert percentage to decimal
        return 1 if ai_prob_decimal >= threshold else 0
    
    def ground_truth_to_binary(gt):
        return 1 if gt == 'ai' else 0
    
    y_true = [ground_truth_to_binary(r['ground_truth']) for r in results]
    y_pred = [prediction_to_binary(r['ai_probability']) for r in results]
    
    # Calculate metrics manually
    total = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / total if total > 0 else 0
    
    # True positives, false positives, true negatives, false negatives
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    cm = [[tn, fp], [fn, tp]]
    
    return {
        'threshold': threshold,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm,
        'tp': tp,
        'fp': fp,
        'tn': tn,
        'fn': fn
    }


def main():
    """Main evaluation function."""
    print("=" * 60)
    print("Multi-Threshold Evaluation")
    print("=" * 60)
    
    # Load benchmark results
    results = load_benchmark_results()
    print(f"Loaded {len(results)} benchmark results")
    print()
    
    # Test different thresholds
    thresholds = [0.50, 0.45, 0.40, 0.35]
    all_metrics = []
    
    for threshold in thresholds:
        print(f"Evaluating at threshold: {threshold}")
        metrics = compute_metrics_at_threshold(results, threshold)
        all_metrics.append(metrics)
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1 Score:  {metrics['f1']:.4f}")
        print(f"  Confusion Matrix: TN={metrics['tn']}, FP={metrics['fp']}, FN={metrics['fn']}, TP={metrics['tp']}")
        print()
    
    # Create comparison table
    print("=" * 60)
    print("Threshold Comparison Table")
    print("=" * 60)
    print(f"{'Threshold':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 60)
    for metrics in all_metrics:
        print(f"{metrics['threshold']:<12.2f} {metrics['accuracy']:<12.4f} {metrics['precision']:<12.4f} {metrics['recall']:<12.4f} {metrics['f1']:<12.4f}")
    print()
    
    # Find best threshold by F1 score
    best_metrics = max(all_metrics, key=lambda x: x['f1'])
    print("=" * 60)
    print(f"Best Threshold: {best_metrics['threshold']:.2f}")
    print("=" * 60)
    print(f"Accuracy:  {best_metrics['accuracy']:.4f}")
    print(f"Precision: {best_metrics['precision']:.4f}")
    print(f"Recall:    {best_metrics['recall']:.4f}")
    print(f"F1 Score:  {best_metrics['f1']:.4f}")
    print(f"Confusion Matrix: TN={best_metrics['tn']}, FP={best_metrics['fp']}, FN={best_metrics['fn']}, TP={best_metrics['tp']}")
    
    # Save detailed report
    with open('threshold_comparison.md', 'w') as f:
        f.write("# Threshold Comparison Report\n\n")
        f.write("## Comparison Table\n\n")
        f.write(f"| Threshold | Accuracy | Precision | Recall | F1 Score |\n")
        f.write("|-----------|----------|-----------|--------|----------|\n")
        for metrics in all_metrics:
            f.write(f"| {metrics['threshold']:.2f} | {metrics['accuracy']:.4f} | {metrics['precision']:.4f} | {metrics['recall']:.4f} | {metrics['f1']:.4f} |\n")
        
        f.write("\n## Best Threshold\n\n")
        f.write(f"**Threshold**: {best_metrics['threshold']:.2f}\n\n")
        f.write(f"- **Accuracy**: {best_metrics['accuracy']:.4f}\n")
        f.write(f"- **Precision**: {best_metrics['precision']:.4f}\n")
        f.write(f"- **Recall**: {best_metrics['recall']:.4f}\n")
        f.write(f"- **F1 Score**: {best_metrics['f1']:.4f}\n\n")
        f.write(f"**Confusion Matrix**:\n")
        f.write(f"```\n")
        f.write(f"              Predicted\n")
        f.write(f"              Human    AI\n")
        f.write(f"Actual Human  {best_metrics['tn']:4d}    {best_metrics['fp']:4d}\n")
        f.write(f"      AI      {best_metrics['fn']:4d}    {best_metrics['tp']:4d}\n")
        f.write(f"```\n")
    
    print()
    print("Detailed report saved to threshold_comparison.md")


if __name__ == "__main__":
    main()

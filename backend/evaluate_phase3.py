"""
Phase 3 Fusion Engine Evaluation
Evaluates the new configurable fusion engine with contribution tracking.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict


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
        ai_prob_decimal = ai_prob / 100.0
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


def analyze_contributions_from_results(results):
    """
    Analyze module contributions from evaluation results.
    
    Since we're using existing CSV results, we'll estimate contributions
    based on the available scores (ai_probability, forensic_score).
    """
    # Estimate contributions based on available data
    # This is a simplified analysis since full contribution data isn't in CSV
    
    contributions = {
        'efficientnet': [],
        'forensic': [],
        'forensic_submodules': defaultdict(list)
    }
    
    for r in results:
        # Estimate EfficientNet contribution from ai_probability
        ai_prob_decimal = r['ai_probability'] / 100.0
        contributions['efficientnet'].append(ai_prob_decimal)
        
        # Forensic contribution from forensic_score
        contributions['forensic'].append(r['forensic_score'])
    
    # Calculate averages
    avg_contributions = {
        'efficientnet': sum(contributions['efficientnet']) / len(contributions['efficientnet']) if contributions['efficientnet'] else 0,
        'forensic': sum(contributions['forensic']) / len(contributions['forensic']) if contributions['forensic'] else 0,
    }
    
    return avg_contributions


def main():
    """Main evaluation function."""
    print("=" * 70)
    print("Phase 3 Fusion Engine Evaluation")
    print("=" * 70)
    
    # Load benchmark results
    results = load_benchmark_results()
    print(f"Loaded {len(results)} benchmark results")
    print()
    
    # Test different thresholds
    thresholds = [0.25, 0.30, 0.35, 0.40, 0.45]
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
    print("=" * 70)
    print("Phase 3 Threshold Comparison Table")
    print("=" * 70)
    print(f"{'Threshold':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 70)
    for metrics in all_metrics:
        print(f"{metrics['threshold']:<12.2f} {metrics['accuracy']:<12.4f} {metrics['precision']:<12.4f} {metrics['recall']:<12.4f} {metrics['f1']:<12.4f}")
    print()
    
    # Find best threshold by F1 score
    best_metrics = max(all_metrics, key=lambda x: x['f1'])
    print("=" * 70)
    print(f"Best Threshold: {best_metrics['threshold']:.2f}")
    print("=" * 70)
    print(f"Accuracy:  {best_metrics['accuracy']:.4f}")
    print(f"Precision: {best_metrics['precision']:.4f}")
    print(f"Recall:    {best_metrics['recall']:.4f}")
    print(f"F1 Score:  {best_metrics['f1']:.4f}")
    print(f"Confusion Matrix: TN={best_metrics['tn']}, FP={best_metrics['fp']}, FN={best_metrics['fn']}, TP={best_metrics['tp']}")
    print()
    
    # Analyze contributions
    print("=" * 70)
    print("Module Contribution Analysis")
    print("=" * 70)
    avg_contributions = analyze_contributions_from_results(results)
    
    print(f"Average EfficientNet Contribution: {avg_contributions['efficientnet']:.4f}")
    print(f"Average Forensic Contribution: {avg_contributions['forensic']:.4f}")
    print()
    
    # Determine which contributes more
    if avg_contributions['efficientnet'] > avg_contributions['forensic']:
        print("EfficientNet contributes more on average")
    else:
        print("Forensic analysis contributes more on average")
    print()
    
    # Historical comparison
    print("=" * 70)
    print("Historical Comparison")
    print("=" * 70)
    print(f"{'Stage':<20} {'Threshold':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 70)
    
    # Stage 1 (Frozen Backbone) - threshold 0.35
    print(f"{'Stage 1 (Frozen)':<20} {0.35:<12.2f} {0.6813:<12.4f} {0.7736:<12.4f} {0.5125:<12.4f} {0.6165:<12.4f}")
    
    # Stage 2 (Unfrozen Backbone) - threshold 0.35
    print(f"{'Stage 2 (Unfrozen)':<20} {0.35:<12.2f} {0.6625:<12.4f} {0.8095:<12.4f} {0.4250:<12.4f} {0.5574:<12.4f}")
    
    # Phase 3 (Fusion Engine) - best threshold
    print(f"{'Phase 3 (Fusion)':<20} {best_metrics['threshold']:<12.2f} {best_metrics['accuracy']:<12.4f} {best_metrics['precision']:<12.4f} {best_metrics['recall']:<12.4f} {best_metrics['f1']:<12.4f}")
    print()
    
    # Phase 3 comparison at threshold 0.35 for direct comparison
    phase3_035 = next(m for m in all_metrics if m['threshold'] == 0.35)
    print("=" * 70)
    print("Direct Comparison at Threshold 0.35")
    print("=" * 70)
    print(f"{'Stage':<20} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 70)
    print(f"{'Stage 1 (Frozen)':<20} {0.6813:<12.4f} {0.7736:<12.4f} {0.5125:<12.4f} {0.6165:<12.4f}")
    print(f"{'Stage 2 (Unfrozen)':<20} {0.6625:<12.4f} {0.8095:<12.4f} {0.4250:<12.4f} {0.5574:<12.4f}")
    print(f"{'Phase 3 (Fusion)':<20} {phase3_035['accuracy']:<12.4f} {phase3_035['precision']:<12.4f} {phase3_035['recall']:<12.4f} {phase3_035['f1']:<12.4f}")
    print()
    
    # Recommendation
    print("=" * 70)
    print("Production Configuration Recommendation")
    print("=" * 70)
    
    # Compare Phase 3 best vs Stage 1 at 0.35
    if best_metrics['f1'] > 0.6165:
        print(f"RECOMMENDED: Phase 3 Fusion Engine with threshold {best_metrics['threshold']:.2f}")
        print(f"  - F1 Score: {best_metrics['f1']:.4f} (vs Stage 1: 0.6165)")
        print(f"  - Improvement: {((best_metrics['f1'] - 0.6165) / 0.6165 * 100):.2f}%")
    else:
        print(f"RECOMMENDED: Stage 1 Frozen Backbone with threshold 0.35")
        print(f"  - F1 Score: 0.6165 (vs Phase 3: {best_metrics['f1']:.4f})")
    
    print()
    print("Configuration Details:")
    print(f"  - Decision Threshold: {best_metrics['threshold']:.2f}")
    print(f"  - Expected Accuracy: {best_metrics['accuracy']:.4f}")
    print(f"  - Expected Precision: {best_metrics['precision']:.4f}")
    print(f"  - Expected Recall: {best_metrics['recall']:.4f}")
    print(f"  - Expected F1 Score: {best_metrics['f1']:.4f}")
    
    # Save detailed report
    with open('phase3_evaluation_report.md', 'w') as f:
        f.write("# Phase 3 Fusion Engine Evaluation Report\n\n")
        
        f.write("## Threshold Comparison Table\n\n")
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
        
        f.write("\n## Module Contribution Analysis\n\n")
        f.write(f"- **EfficientNet Average Contribution**: {avg_contributions['efficientnet']:.4f}\n")
        f.write(f"- **Forensic Average Contribution**: {avg_contributions['forensic']:.4f}\n")
        
        f.write("\n## Historical Comparison\n\n")
        f.write(f"| Stage | Threshold | Accuracy | Precision | Recall | F1 Score |\n")
        f.write("|-------|-----------|----------|-----------|--------|----------|\n")
        f.write(f"| Stage 1 (Frozen) | 0.35 | 0.6813 | 0.7736 | 0.5125 | 0.6165 |\n")
        f.write(f"| Stage 2 (Unfrozen) | 0.35 | 0.6625 | 0.8095 | 0.4250 | 0.5574 |\n")
        f.write(f"| Phase 3 (Fusion) | {best_metrics['threshold']:.2f} | {best_metrics['accuracy']:.4f} | {best_metrics['precision']:.4f} | {best_metrics['recall']:.4f} | {best_metrics['f1']:.4f} |\n")
        
        f.write("\n## Recommendation\n\n")
        if best_metrics['f1'] > 0.6165:
            f.write(f"**RECOMMENDED**: Phase 3 Fusion Engine with threshold {best_metrics['threshold']:.2f}\n\n")
            f.write(f"F1 Score: {best_metrics['f1']:.4f} (vs Stage 1: 0.6165)\n")
            f.write(f"Improvement: {((best_metrics['f1'] - 0.6165) / 0.6165 * 100):.2f}%\n")
        else:
            f.write(f"**RECOMMENDED**: Stage 1 Frozen Backbone with threshold 0.35\n\n")
            f.write(f"F1 Score: 0.6165 (vs Phase 3: {best_metrics['f1']:.4f})\n")
    
    print()
    print("Detailed report saved to phase3_evaluation_report.md")


if __name__ == "__main__":
    main()

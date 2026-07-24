"""
Phase 3 Full Evaluation with Real Fusion Engine
Runs benchmark through the new configurable fusion engine to get actual contribution data.
"""

import asyncio
import json
import csv
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent))

from app.ai.detectors.image_detector import analyze_image


async def run_full_evaluation():
    """Run full evaluation with the new fusion engine."""
    
    benchmark_dir = Path("benchmark")
    if not benchmark_dir.exists():
        print("Benchmark directory not found")
        return None, None
    
    # Get all images from benchmark directory (including subdirectories)
    image_files = list(benchmark_dir.glob("**/*.jpg")) + list(benchmark_dir.glob("**/*.png"))
    
    if not image_files:
        print("No images found in benchmark directory")
        return None, None
    
    print(f"Found {len(image_files)} images in benchmark directory")
    
    # Load ground truth from existing CSV
    ground_truth = {}
    csv_path = "benchmark_trained.csv"
    if Path(csv_path).exists():
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ground_truth[row['filename']] = row['ground_truth']
    
    results = []
    contributions_data = []
    
    for image_path in image_files:
        filename = image_path.name
        print(f"Analyzing: {filename}")
        
        try:
            result = await analyze_image(str(image_path))
            
            # Extract relevant data
            ai_prob = result.get('ai_probability', 0) / 100.0  # Convert to decimal
            ground = ground_truth.get(filename, 'unknown')
            
            results.append({
                'filename': filename,
                'ground_truth': ground,
                'ai_probability': ai_prob,
                'verdict': result.get('verdict'),
                'confidence': result.get('confidence'),
                'contributions': result.get('module_contributions', {})
            })
            
            contributions_data.append(result.get('module_contributions', {}))
            
        except Exception as e:
            print(f"Error analyzing {filename}: {e}")
    
    # Save results with contributions
    with open('phase3_results_with_contributions.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Analyzed {len(results)} images successfully")
    print("Results saved to phase3_results_with_contributions.json")
    
    return results, contributions_data


def compute_metrics_at_threshold(results, threshold: float):
    """Compute metrics at a specific threshold."""
    def prediction_to_binary(ai_prob):
        return 1 if ai_prob >= threshold else 0
    
    def ground_truth_to_binary(gt):
        return 1 if gt == 'ai' else 0
    
    y_true = [ground_truth_to_binary(r['ground_truth']) for r in results]
    y_pred = [prediction_to_binary(r['ai_probability']) for r in results]
    
    total = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = correct / total if total > 0 else 0
    
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'threshold': threshold,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'tp': tp,
        'fp': fp,
        'tn': tn,
        'fn': fn
    }


def analyze_contributions(contributions_data):
    """Analyze module contributions from real fusion engine data."""
    
    # Initialize accumulators
    whole_image_contribs = []
    face_contribs = []
    forensic_contribs = []
    
    forensic_submodules = defaultdict(list)
    
    for contrib in contributions_data:
        if not contrib:
            continue
        
        # Main module contributions
        if 'whole_image' in contrib:
            whole_image_contribs.append(contrib['whole_image'].get('contribution', 0))
        
        if 'face' in contrib:
            face_contribs.append(contrib['face'].get('contribution', 0))
        
        if 'forensic' in contrib:
            forensic_contribs.append(contrib['forensic'].get('contribution', 0))
            
            # Sub-module contributions
            sub_modules = contrib['forensic'].get('sub_modules', {})
            for module, value in sub_modules.items():
                forensic_submodules[module].append(value)
    
    # Calculate averages
    avg_contributions = {
        'whole_image': sum(whole_image_contribs) / len(whole_image_contribs) if whole_image_contribs else 0,
        'face': sum(face_contribs) / len(face_contribs) if face_contribs else 0,
        'forensic': sum(forensic_contribs) / len(forensic_contribs) if forensic_contribs else 0,
    }
    
    # Calculate sub-module averages
    avg_forensic_submodules = {}
    for module, values in forensic_submodules.items():
        avg_forensic_submodules[module] = sum(values) / len(values) if values else 0
    
    return avg_contributions, avg_forensic_submodules


async def main():
    """Main evaluation function."""
    print("=" * 70)
    print("Phase 3 Full Fusion Engine Evaluation")
    print("=" * 70)
    print()
    
    # Run full evaluation with real fusion engine
    results, contributions_data = await run_full_evaluation()
    
    if not results:
        print("No results to analyze")
        return
    
    print()
    print("=" * 70)
    print("Threshold Evaluation")
    print("=" * 70)
    
    # Test different thresholds
    thresholds = [0.25, 0.30, 0.35, 0.40, 0.45]
    all_metrics = []
    
    for threshold in thresholds:
        metrics = compute_metrics_at_threshold(results, threshold)
        all_metrics.append(metrics)
        print(f"Threshold {threshold:.2f}: Acc={metrics['accuracy']:.4f}, Prec={metrics['precision']:.4f}, Rec={metrics['recall']:.4f}, F1={metrics['f1']:.4f}")
    
    print()
    print("=" * 70)
    print("Threshold Comparison Table")
    print("=" * 70)
    print(f"{'Threshold':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 70)
    for metrics in all_metrics:
        print(f"{metrics['threshold']:<12.2f} {metrics['accuracy']:<12.4f} {metrics['precision']:<12.4f} {metrics['recall']:<12.4f} {metrics['f1']:<12.4f}")
    
    # Find best threshold
    best_metrics = max(all_metrics, key=lambda x: x['f1'])
    print()
    print(f"Best Threshold: {best_metrics['threshold']:.2f} (F1: {best_metrics['f1']:.4f})")
    
    print()
    print("=" * 70)
    print("Module Contribution Analysis")
    print("=" * 70)
    
    avg_contributions, avg_forensic_submodules = analyze_contributions(contributions_data)
    
    print(f"Average Contributions:")
    print(f"  EfficientNet (whole_image): {avg_contributions['whole_image']:.4f}")
    print(f"  Face Detector: {avg_contributions['face']:.4f}")
    print(f"  Forensic Bundle: {avg_contributions['forensic']:.4f}")
    print()
    
    print(f"Forensic Sub-module Contributions:")
    for module, avg in sorted(avg_forensic_submodules.items(), key=lambda x: x[1], reverse=True):
        print(f"  {module}: {avg:.4f}")
    
    print()
    
    # Find most/least contributing
    main_modules = {
        'EfficientNet': avg_contributions['whole_image'],
        'Face Detector': avg_contributions['face'],
        'Forensic Bundle': avg_contributions['forensic']
    }
    
    most_contributing = max(main_modules.items(), key=lambda x: x[1])
    least_contributing = min(main_modules.items(), key=lambda x: x[1])
    
    print(f"Most Contributing Module: {most_contributing[0]} ({most_contributing[1]:.4f})")
    print(f"Least Contributing Module: {least_contributing[0]} ({least_contributing[1]:.4f})")
    
    if avg_forensic_submodules:
        most_forensic = max(avg_forensic_submodules.items(), key=lambda x: x[1])
        least_forensic = min(avg_forensic_submodules.items(), key=lambda x: x[1])
        print(f"Most Contributing Forensic Module: {most_forensic[0]} ({most_forensic[1]:.4f})")
        print(f"Least Contributing Forensic Module: {least_forensic[0]} ({least_forensic[1]:.4f})")
    
    print()
    print("=" * 70)
    print("Historical Comparison")
    print("=" * 70)
    print(f"{'Stage':<20} {'Threshold':<12} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 70)
    print(f"{'Stage 1 (Frozen)':<20} {0.35:<12.2f} {0.6813:<12.4f} {0.7736:<12.4f} {0.5125:<12.4f} {0.6165:<12.4f}")
    print(f"{'Stage 2 (Unfrozen)':<20} {0.35:<12.2f} {0.6625:<12.4f} {0.8095:<12.4f} {0.4250:<12.4f} {0.5574:<12.4f}")
    print(f"{'Phase 3 (Fusion)':<20} {best_metrics['threshold']:<12.2f} {best_metrics['accuracy']:<12.4f} {best_metrics['precision']:<12.4f} {best_metrics['recall']:<12.4f} {best_metrics['f1']:<12.4f}")
    
    print()
    print("=" * 70)
    print("Production Configuration Recommendation")
    print("=" * 70)
    
    if best_metrics['f1'] > 0.6165:
        print(f"RECOMMENDED: Phase 3 Fusion Engine with threshold {best_metrics['threshold']:.2f}")
        print(f"  - F1 Score: {best_metrics['f1']:.4f} (vs Stage 1: 0.6165)")
        improvement = ((best_metrics['f1'] - 0.6165) / 0.6165 * 100)
        print(f"  - Improvement: {improvement:.2f}%")
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


if __name__ == "__main__":
    asyncio.run(main())

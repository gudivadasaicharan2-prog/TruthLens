"""
Benchmark Dataset Creation and Evaluation
==========================================
Creates a balanced benchmark dataset from AI_vs_Human and evaluates the detector.
"""

import csv
import shutil
from pathlib import Path
import random
import sys
import os
import asyncio

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.ai.detectors.image_detector import analyze_image


def create_benchmark_dataset(
    csv_path: str = r"C:\Users\LENOVO\Downloads\AI_Datasets\AI_vs_Human\train.csv",
    data_root: str = r"C:\Users\LENOVO\Downloads\AI_Datasets\AI_vs_Human",
    output_dir: str = "benchmark",
    sample_size: int = 160,
    random_seed: int = 42
):
    """
    Create balanced benchmark dataset from AI_vs_Human.
    
    Args:
        csv_path: Path to train.csv
        data_root: Root directory containing train_data
        output_dir: Output directory for benchmark
        sample_size: Total number of images (will be split 50/50)
        random_seed: Random seed for reproducibility
    """
    random.seed(random_seed)
    
    print("=" * 60)
    print("Creating Benchmark Dataset")
    print("=" * 60)
    print(f"CSV path: {csv_path}")
    print(f"Data root: {data_root}")
    print(f"Output: {output_dir}")
    print(f"Sample size: {sample_size}")
    print()
    
    # Read CSV
    human_images = []
    ai_images = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_name = row['file_name']
            label = int(row['label'])
            if label == 0:
                human_images.append(file_name)
            else:
                ai_images.append(file_name)
    
    print(f"Total images in CSV: {len(human_images) + len(ai_images)}")
    print(f"Human images (label=0): {len(human_images)}")
    print(f"AI images (label=1): {len(ai_images)}")
    print()
    
    # Sample balanced dataset
    samples_per_class = sample_size // 2
    
    human_sample = random.sample(human_images, min(samples_per_class, len(human_images)))
    ai_sample = random.sample(ai_images, min(samples_per_class, len(ai_images)))
    
    print(f"Sampled {len(human_sample)} human images")
    print(f"Sampled {len(ai_sample)} AI images")
    print()
    
    # Create output directories
    output_path = Path(output_dir)
    human_dir = output_path / "human"
    ai_dir = output_path / "ai"
    
    # Delete old benchmark if exists
    if output_path.exists():
        print(f"Deleting old benchmark directory: {output_path}")
        shutil.rmtree(output_path)
    
    human_dir.mkdir(parents=True, exist_ok=True)
    ai_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy human images
    print("Copying human images...")
    human_copied = 0
    for file_name in human_sample:
        src_path = Path(data_root) / file_name
        if src_path.exists():
            dst_path = human_dir / src_path.name
            shutil.copy2(src_path, dst_path)
            human_copied += 1
        else:
            print(f"  WARNING: {src_path} not found")
    
    # Copy AI images
    print("Copying AI images...")
    ai_copied = 0
    for file_name in ai_sample:
        src_path = Path(data_root) / file_name
        if src_path.exists():
            dst_path = ai_dir / src_path.name
            shutil.copy2(src_path, dst_path)
            ai_copied += 1
        else:
            print(f"  WARNING: {src_path} not found")
    
    print()
    print(f"Copied {human_copied} human images")
    print(f"Copied {ai_copied} AI images")
    print(f"Total: {human_copied + ai_copied} images")
    print()
    
    # Save sample info for evaluation
    with open(output_path / "benchmark_metadata.csv", 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['file_name', 'label'])
        for file_name in human_sample:
            writer.writerow([file_name, 0])
        for file_name in ai_sample:
            writer.writerow([file_name, 1])
    
    return human_copied, ai_copied


async def evaluate_benchmark(
    benchmark_dir: str = "benchmark",
    output_csv: str = "benchmark.csv"
):
    """
    Evaluate all images in benchmark directory.
    
    Args:
        benchmark_dir: Directory containing human/ and ai/ subdirectories
        output_csv: Path to output CSV with predictions
    """
    print("=" * 60)
    print("Evaluating Benchmark Images")
    print("=" * 60)
    
    benchmark_path = Path(benchmark_dir)
    results = []
    
    # Evaluate human images
    human_dir = benchmark_path / "human"
    if human_dir.exists():
        print(f"Evaluating human images ({len(list(human_dir.glob('*')))} files)...")
        for img_path in human_dir.glob("*"):
            if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    result = await analyze_image(str(img_path))
                    results.append({
                        'filename': img_path.name,
                        'ground_truth': 'human',
                        'prediction': result.get('verdict', 'unknown'),
                        'confidence': result.get('confidence', 0.0),
                        'ai_probability': result.get('ai_probability', 0.0),
                        'forensic_score': result.get('forensic_score', 0.0)
                    })
                    print(f"  {img_path.name}: {result.get('verdict', 'unknown')} (conf: {result.get('confidence', 0.0):.3f})")
                except Exception as e:
                    print(f"  ERROR processing {img_path.name}: {e}")
                    results.append({
                        'filename': img_path.name,
                        'ground_truth': 'human',
                        'prediction': 'error',
                        'confidence': 0.0,
                        'ai_probability': 0.0,
                        'forensic_score': 0.0
                    })
    
    # Evaluate AI images
    ai_dir = benchmark_path / "ai"
    if ai_dir.exists():
        print(f"Evaluating AI images ({len(list(ai_dir.glob('*')))} files)...")
        for img_path in ai_dir.glob("*"):
            if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                try:
                    result = await analyze_image(str(img_path))
                    results.append({
                        'filename': img_path.name,
                        'ground_truth': 'ai',
                        'prediction': result.get('verdict', 'unknown'),
                        'confidence': result.get('confidence', 0.0),
                        'ai_probability': result.get('ai_probability', 0.0),
                        'forensic_score': result.get('forensic_score', 0.0)
                    })
                    print(f"  {img_path.name}: {result.get('verdict', 'unknown')} (conf: {result.get('confidence', 0.0):.3f})")
                except Exception as e:
                    print(f"  ERROR processing {img_path.name}: {e}")
                    results.append({
                        'filename': img_path.name,
                        'ground_truth': 'ai',
                        'prediction': 'error',
                        'confidence': 0.0,
                        'ai_probability': 0.0,
                        'forensic_score': 0.0
                    })
    
    # Save results
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'ground_truth', 'prediction', 'confidence', 'ai_probability', 'forensic_score'])
        for result in results:
            writer.writerow([
                result['filename'],
                result['ground_truth'],
                result['prediction'],
                result['confidence'],
                result['ai_probability'],
                result['forensic_score']
            ])
    
    print()
    print(f"Results saved to {output_csv}")
    print(f"Total evaluated: {len(results)}")
    
    return results


def compute_metrics(results):
    """
    Compute evaluation metrics.
    
    Args:
        results: List of evaluation result dictionaries
    """
    print("=" * 60)
    print("Computing Metrics")
    print("=" * 60)
    
    # Convert predictions to binary (AI=1, Human=0)
    def prediction_to_binary(pred):
        if pred in ['AI Generated', 'Likely AI Generated', 'Deepfake Detected']:
            return 1
        elif pred in ['Authentic', 'Likely Authentic']:
            return 0
        else:
            return 0  # Default to human for unknown
    
    def ground_truth_to_binary(gt):
        return 1 if gt == 'ai' else 0
    
    y_true = [ground_truth_to_binary(r['ground_truth']) for r in results]
    y_pred = [prediction_to_binary(r['prediction']) for r in results]
    
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
    
    print(f"Accuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print()
    print("Confusion Matrix:")
    print(f"  TN={cm[0][0]:4d}  FP={cm[0][1]:4d}")
    print(f"  FN={cm[1][0]:4d}  TP={cm[1][1]:4d}")
    print()
    
    # False positives and false negatives
    fp_results = [r for r, t, p in zip(results, y_true, y_pred) if t == 0 and p == 1]
    fn_results = [r for r, t, p in zip(results, y_true, y_pred) if t == 1 and p == 0]
    
    print(f"False Positives (Human misclassified as AI): {len(fp_results)}")
    if len(fp_results) > 0:
        for r in fp_results[:10]:
            print(f"  - {r['filename']}: {r['prediction']} (AI prob: {r['ai_probability']:.3f})")
    
    print()
    print(f"False Negatives (AI misclassified as Human): {len(fn_results)}")
    if len(fn_results) > 0:
        for r in fn_results[:10]:
            print(f"  - {r['filename']}: {r['prediction']} (AI prob: {r['ai_probability']:.3f})")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm,
        'false_positives': fp_results,
        'false_negatives': fn_results
    }


def generate_report(metrics: dict, results, output_path: str = "benchmark_report.md"):
    """
    Generate benchmark report.
    
    Args:
        metrics: Dictionary of computed metrics
        results: List of evaluation result dictionaries
        output_path: Path to output report
    """
    print("=" * 60)
    print("Generating Report")
    print("=" * 60)
    
    human_count = sum(1 for r in results if r['ground_truth'] == 'human')
    ai_count = sum(1 for r in results if r['ground_truth'] == 'ai')
    
    report = f"""# TruthLens Benchmark Report

## Dataset Information

- **Source**: AI_vs_Human (Women in AI Kaggle dataset)
- **Total Images**: {len(results)}
- **Human Images**: {human_count}
- **AI Images**: {ai_count}
- **Sample Size**: 160 (80 human, 80 AI)

## Evaluation Metrics

- **Accuracy**: {metrics['accuracy']:.4f}
- **Precision**: {metrics['precision']:.4f}
- **Recall**: {metrics['recall']:.4f}
- **F1 Score**: {metrics['f1']:.4f}

## Confusion Matrix

```
              Predicted
              Human    AI
Actual Human  {metrics['confusion_matrix'][0][0]:4d}    {metrics['confusion_matrix'][0][1]:4d}
      AI      {metrics['confusion_matrix'][1][0]:4d}    {metrics['confusion_matrix'][1][1]:4d}
```

## False Positives (Human misclassified as AI)

Total: {len(metrics['false_positives'])}

"""
    
    if len(metrics['false_positives']) > 0:
        for r in metrics['false_positives']:
            report += f"- {r['filename']}: {r['prediction']} (AI prob: {r['ai_probability']:.3f}, confidence: {r['confidence']:.3f})\n"
    else:
        report += "None\n"
    
    report += "\n## False Negatives (AI misclassified as Human)\n\n"
    report += f"Total: {len(metrics['false_negatives'])}\n\n"
    
    if len(metrics['false_negatives']) > 0:
        for r in metrics['false_negatives']:
            report += f"- {r['filename']}: {r['prediction']} (AI prob: {r['ai_probability']:.3f}, confidence: {r['confidence']:.3f})\n"
    else:
        report += "None\n"
    
    report += "\n## Model Configuration\n\n"
    report += "- **Backbone**: EfficientNet-B2 (ImageNet pretrained, frozen)\n"
    report += "- **Classifier Head**: MLP (1408 -> 512 -> 1)\n"
    report += "- **Input Size**: 224x224\n"
    report += "- **Forensic Modules**: ELA, Noise, Frequency, Texture, Edge, Color, EXIF\n"
    report += "- **Face Detection**: MTCNN\n"
    
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"Report saved to {output_path}")


async def main():
    """Main execution function."""
    # Step 1: Create benchmark dataset
    human_count, ai_count = create_benchmark_dataset()
    
    if human_count + ai_count == 0:
        print("ERROR: No images copied to benchmark. Exiting.")
        return
    
    # Step 2: Evaluate benchmark
    results = await evaluate_benchmark()
    
    # Step 3: Compute metrics
    metrics = compute_metrics(results)
    
    # Step 4: Generate report
    generate_report(metrics, results)
    
    print()
    print("=" * 60)
    print("Benchmark Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

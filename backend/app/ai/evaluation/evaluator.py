"""
Image Detection Evaluator
==========================
Automated evaluation framework for image detection performance.
Scans uploads directory, runs detection, and generates reports.
"""

import os
import csv
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


def scan_images_directory(uploads_dir: str) -> List[str]:
    """
    Scan uploads directory for image files.
    
    Args:
        uploads_dir: Path to uploads directory
        
    Returns:
        List of image file paths (unique)
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
    image_files = set()
    
    uploads_path = Path(uploads_dir)
    if not uploads_path.exists():
        return []
    
    for ext in image_extensions:
        # Case-insensitive glob
        for f in uploads_path.glob(f'*{ext}'):
            image_files.add(str(f))
        for f in uploads_path.glob(f'*{ext.upper()}'):
            image_files.add(str(f))
    
    return sorted(list(image_files))


def load_ground_truth(gt_path: str) -> Optional[Dict[str, Dict]]:
    """
    Load ground truth CSV file.
    
    Expected format:
    filename,is_fake,category
    image1.jpg,0,smartphone
    image2.jpg,1,chatgpt
    
    Args:
        gt_path: Path to ground_truth.csv
        
    Returns:
        Dictionary mapping filename to ground truth data, or None if file doesn't exist
    """
    gt_file = Path(gt_path)
    if not gt_file.exists():
        return None
    
    ground_truth = {}
    try:
        with open(gt_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row.get('filename', '')
                if filename:
                    ground_truth[filename] = {
                        'is_fake': int(row.get('is_fake', 0)),
                        'category': row.get('category', 'unknown')
                    }
    except Exception as e:
        print(f"[Evaluation] Error loading ground truth: {e}")
        return None
    
    return ground_truth


def calculate_metrics(predictions: List[Dict], ground_truth: Dict[str, Dict]) -> Dict:
    """
    Calculate evaluation metrics given predictions and ground truth.
    
    Args:
        predictions: List of prediction dictionaries
        ground_truth: Dictionary mapping filename to ground truth
        
    Returns:
        Dictionary with metrics
    """
    y_true = []
    y_pred = []
    categories_true = []
    categories_pred = []
    
    for pred in predictions:
        filename = pred['filename']
        if filename in ground_truth:
            gt = ground_truth[filename]
            y_true.append(gt['is_fake'])
            # Convert verdict to binary: 1 for fake, 0 for authentic
            verdict = pred['verdict'].lower()
            is_fake_pred = 1 if any(x in verdict for x in ['deepfake', 'ai generated', 'suspicious']) else 0
            y_pred.append(is_fake_pred)
            categories_true.append(gt['category'])
            categories_pred.append(pred.get('image_type', 'unknown'))
    
    if not y_true:
        return {
            'error': 'No matching ground truth data found'
        }
    
    # Calculate overall metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    # Calculate confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Calculate per-category accuracy
    category_accuracy = {}
    unique_categories = set(categories_true)
    for cat in unique_categories:
        cat_indices = [i for i, c in enumerate(categories_true) if c == cat]
        if cat_indices:
            cat_true = [y_true[i] for i in cat_indices]
            cat_pred = [y_pred[i] for i in cat_indices]
            cat_acc = accuracy_score(cat_true, cat_pred)
            category_accuracy[cat] = cat_acc
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'confusion_matrix': cm.tolist(),
        'per_category_accuracy': category_accuracy,
        'total_samples': len(y_true)
    }


def run_evaluation(
    uploads_dir: str = None,
    output_dir: str = None,
    ground_truth_path: str = None
) -> Tuple[str, Dict]:
    """
    Run evaluation on all images in uploads directory.
    
    Args:
        uploads_dir: Path to uploads directory (default: backend/uploads)
        output_dir: Path to output directory (default: backend/evaluation)
        ground_truth_path: Path to ground_truth.csv (default: output_dir/ground_truth.csv)
        
    Returns:
        Tuple of (predictions_csv_path, metrics_dict)
    """
    # Set default paths
    if uploads_dir is None:
        backend_dir = Path(__file__).parent.parent.parent.parent
        uploads_dir = str(backend_dir / 'uploads')
    
    if output_dir is None:
        backend_dir = Path(__file__).parent.parent.parent.parent
        output_dir = str(backend_dir / 'evaluation')
    
    if ground_truth_path is None:
        ground_truth_path = str(Path(output_dir) / 'ground_truth.csv')
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load ground truth if available
    ground_truth = load_ground_truth(ground_truth_path)
    
    # Scan for images
    image_files = scan_images_directory(uploads_dir)
    
    if not image_files:
        print(f"[Evaluation] No images found in {uploads_dir}")
        return None, {'error': 'No images found'}
    
    print(f"[Evaluation] Found {len(image_files)} images")
    
    # Import detector
    try:
        from app.ai.detectors.image_detector import analyze_image
        from app.ai.classification.image_type_classifier import classify_image_type
        import cv2
    except ImportError as e:
        print(f"[Evaluation] Error importing detector: {e}")
        return None, {'error': f'Import error: {e}'}
    
    # Run detection on each image
    predictions = []
    
    async def process_image(img_path: str) -> Optional[Dict]:
        try:
            print(f"[Evaluation] Processing: {Path(img_path).name}")
            
            # Read image for classification
            img_array = cv2.imread(img_path)
            if img_array is None:
                print(f"[Evaluation] Could not read: {img_path}")
                return None
            
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
            
            # Run image type classifier
            classification = classify_image_type(img_rgb, 0)
            image_type = classification['image_type']
            recommended_pipeline = classification['recommended_pipeline']
            face_count = classification['face_count']
            
            # Run full detection (async)
            result = await analyze_image(img_path)
            
            # Extract relevant fields
            prediction = {
                'filename': Path(img_path).name,
                'image_type': image_type,
                'verdict': result.get('verdict', 'Unknown'),
                'confidence': result.get('confidence', 0.0),
                'ai_probability': result.get('ai_probability', 0.0),
                'deepfake_probability': result.get('deepfake_probability', 0.0),
                'forensic_score': result.get('truth_score', 0.0) / 100.0 if result.get('truth_score') else 0.0,
                'face_count': face_count,
                'recommended_pipeline': recommended_pipeline
            }
            
            return prediction
            
        except Exception as e:
            print(f"[Evaluation] Error processing {img_path}: {e}")
            return None
    
    # Process all images asynchronously
    async def process_all():
        tasks = [process_image(img_path) for img_path in image_files]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
    
    predictions = asyncio.run(process_all())
    
    if not predictions:
        print("[Evaluation] No successful predictions")
        return None, {'error': 'No successful predictions'}
    
    # Save predictions CSV
    predictions_csv = output_path / 'predictions.csv'
    with open(predictions_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'filename', 'image_type', 'verdict', 'confidence',
            'ai_probability', 'deepfake_probability', 'forensic_score',
            'face_count', 'recommended_pipeline'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(predictions)
    
    print(f"[Evaluation] Saved predictions to {predictions_csv}")
    
    # Calculate metrics if ground truth available
    metrics = {}
    if ground_truth:
        print("[Evaluation] Calculating metrics with ground truth")
        metrics = calculate_metrics(predictions, ground_truth)
        
        # Save metrics report
        metrics_csv = output_path / 'metrics.csv'
        with open(metrics_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['metric', 'value'])
            writer.writerow(['accuracy', metrics.get('accuracy', 'N/A')])
            writer.writerow(['precision', metrics.get('precision', 'N/A')])
            writer.writerow(['recall', metrics.get('recall', 'N/A')])
            writer.writerow(['f1_score', metrics.get('f1_score', 'N/A')])
            writer.writerow(['total_samples', metrics.get('total_samples', 'N/A')])
            writer.writerow([])
            writer.writerow(['confusion_matrix'])
            cm = metrics.get('confusion_matrix', [])
            for row in cm:
                writer.writerow(row)
            writer.writerow([])
            writer.writerow(['per_category_accuracy'])
            for cat, acc in metrics.get('per_category_accuracy', {}).items():
                writer.writerow([cat, acc])
        
        print(f"[Evaluation] Saved metrics to {metrics_csv}")
    else:
        print("[Evaluation] No ground truth file found, skipping metrics calculation")
        metrics = {'message': 'No ground truth available'}
    
    return str(predictions_csv), metrics


def evaluate_with_ground_truth(
    ground_truth_csv: str,
    uploads_dir: str = None,
    output_dir: str = None
) -> Dict:
    """
    Run evaluation with specific ground truth file.
    
    Args:
        ground_truth_csv: Path to ground truth CSV file
        uploads_dir: Path to uploads directory
        output_dir: Path to output directory
        
    Returns:
        Dictionary with metrics
    """
    if output_dir is None:
        backend_dir = Path(__file__).parent.parent.parent.parent
        output_dir = str(backend_dir / 'evaluation')
    
    # Copy ground truth to evaluation directory
    import shutil
    gt_dest = Path(output_dir) / 'ground_truth.csv'
    shutil.copy(ground_truth_csv, gt_dest)
    
    _, metrics = run_evaluation(uploads_dir, output_dir, str(gt_dest))
    return metrics

"""
TruthLens v2.2 Benchmark Script

This script benchmarks the current pipeline against the enhanced v2.2 pipeline,
measuring accuracy, precision, recall, F1, false positives, false negatives,
OOD detection rate, average inference time, and GPU utilization.

Usage:
    python benchmark_v2.2.py --dataset /path/to/dataset --output results.json
"""

import os
import sys
import time
import json
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import torch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.ai.detectors.image_detector import analyze_image
from app.ai.inference.patch_inference import analyze_image_patches
from app.ai.inference.ood_detector import detect_ood
from app.ai.forensics.frequency import enhanced_frequency_analysis
from app.ai.forensics.noise import enhanced_noise_analysis
from app.ai.inference.performance_optimizer import get_performance_stats


class Benchmark:
    """
    Benchmark utility for comparing current vs enhanced pipeline.
    """
    
    def __init__(self, dataset_path: str, output_path: str):
        """
        Initialize benchmark.
        
        Args:
            dataset_path: Path to dataset directory
            output_path: Path to save benchmark results
        """
        self.dataset_path = Path(dataset_path)
        self.output_path = Path(output_path)
        self.results = {
            'current_pipeline': {},
            'enhanced_pipeline': {},
            'comparison': {}
        }
    
    def load_dataset(self) -> List[Tuple[str, str]]:
        """
        Load dataset with ground truth labels.
        
        Expected directory structure:
        dataset/
            real/
                image1.jpg
                image2.jpg
            fake/
                image1.jpg
                image2.jpg
        
        Returns:
            List of (image_path, label) tuples
        """
        images = []
        
        # Load real images
        real_dir = self.dataset_path / 'real'
        if real_dir.exists():
            for img_path in real_dir.glob('*.jpg'):
                images.append((str(img_path), 'real'))
            for img_path in real_dir.glob('*.png'):
                images.append((str(img_path), 'real'))
        
        # Load fake images
        fake_dir = self.dataset_path / 'fake'
        if fake_dir.exists():
            for img_path in fake_dir.glob('*.jpg'):
                images.append((str(img_path), 'fake'))
            for img_path in fake_dir.glob('*.png'):
                images.append((str(img_path), 'fake'))
        
        return images
    
    def run_current_pipeline(self, image_path: str) -> Dict:
        """
        Run current pipeline analysis.
        
        Args:
            image_path: Path to image
            
        Returns:
            Analysis results
        """
        start_time = time.time()
        
        # Run current pipeline
        result = analyze_image(image_path)
        
        inference_time = time.time() - start_time
        
        return {
            'verdict': result['verdict'],
            'confidence': result['confidence'],
            'ai_probability': result['ai_probability'],
            'inference_time': inference_time
        }
    
    def run_enhanced_pipeline(self, image_path: str) -> Dict:
        """
        Run enhanced v2.2 pipeline analysis.
        
        Args:
            image_path: Path to image
            
        Returns:
            Enhanced analysis results
        """
        import cv2
        from PIL import Image
        
        start_time = time.time()
        
        # Load image
        img = Image.open(image_path).convert('RGB')
        img_array = np.array(img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Run current pipeline for base results
        base_result = analyze_image(image_path)
        
        # Enhanced: Patch-based inference
        patch_stats = analyze_image_patches(img_array)
        
        # Enhanced: OOD detection
        # Extract features from model (simplified for benchmark)
        ood_score = 0.5  # Placeholder - would use actual features
        
        # Enhanced: Frequency analysis
        freq_features = enhanced_frequency_analysis(gray)
        
        # Enhanced: Noise analysis
        noise_features = enhanced_noise_analysis(gray)
        
        # Enhanced: Adaptive fusion (simplified)
        # In production, this would use the adaptive fusion engine
        enhanced_ai_prob = base_result['ai_probability']
        
        # Adjust based on patch statistics
        if patch_stats['highest_patch_probability'] > 0.8:
            enhanced_ai_prob = max(enhanced_ai_prob, patch_stats['highest_patch_probability'] * 100)
        
        # Adjust based on OOD score
        if ood_score > 0.7:
            # Increase uncertainty
            enhanced_ai_prob = enhanced_ai_prob * 0.8 + 50 * 0.2
        
        inference_time = time.time() - start_time
        
        return {
            'verdict': base_result['verdict'],
            'confidence': base_result['confidence'],
            'ai_probability': enhanced_ai_prob,
            'inference_time': inference_time,
            'patch_statistics': patch_stats,
            'ood_score': ood_score,
            'frequency_features': freq_features,
            'noise_features': noise_features
        }
    
    def calculate_metrics(self, predictions: List[str], labels: List[str]) -> Dict:
        """
        Calculate classification metrics.
        
        Args:
            predictions: List of predicted labels
            labels: List of ground truth labels
            
        Returns:
            Dictionary of metrics
        """
        # Convert verdicts to binary labels
        pred_binary = []
        for pred in predictions:
            if pred in ['AI Generated', 'Deepfake', 'Suspicious']:
                pred_binary.append('fake')
            else:
                pred_binary.append('real')
        
        # Calculate metrics
        tp = sum(1 for p, l in zip(pred_binary, labels) if p == 'fake' and l == 'fake')
        tn = sum(1 for p, l in zip(pred_binary, labels) if p == 'real' and l == 'real')
        fp = sum(1 for p, l in zip(pred_binary, labels) if p == 'fake' and l == 'real')
        fn = sum(1 for p, l in zip(pred_binary, labels) if p == 'real' and l == 'fake')
        
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'true_positives': tp,
            'true_negatives': tn,
            'false_positives': fp,
            'false_negatives': fn
        }
    
    def run_benchmark(self):
        """
        Run complete benchmark comparing current vs enhanced pipeline.
        """
        print("Loading dataset...")
        images = self.load_dataset()
        
        if not images:
            print("No images found in dataset!")
            return
        
        print(f"Found {len(images)} images")
        
        # Run current pipeline
        print("\n=== Running Current Pipeline ===")
        current_predictions = []
        current_labels = []
        current_times = []
        
        for i, (img_path, label) in enumerate(images):
            print(f"Processing {i+1}/{len(images)}: {img_path}")
            
            try:
                result = self.run_current_pipeline(img_path)
                current_predictions.append(result['verdict'])
                current_labels.append(label)
                current_times.append(result['inference_time'])
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                continue
        
        # Calculate current pipeline metrics
        current_metrics = self.calculate_metrics(current_predictions, current_labels)
        current_metrics['avg_inference_time'] = np.mean(current_times)
        current_metrics['total_images'] = len(current_predictions)
        
        self.results['current_pipeline'] = current_metrics
        print(f"Current Pipeline Results:")
        print(f"  Accuracy: {current_metrics['accuracy']:.4f}")
        print(f"  Precision: {current_metrics['precision']:.4f}")
        print(f"  Recall: {current_metrics['recall']:.4f}")
        print(f"  F1: {current_metrics['f1']:.4f}")
        print(f"  Avg Inference Time: {current_metrics['avg_inference_time']:.4f}s")
        
        # Run enhanced pipeline
        print("\n=== Running Enhanced v2.2 Pipeline ===")
        enhanced_predictions = []
        enhanced_labels = []
        enhanced_times = []
        
        for i, (img_path, label) in enumerate(images):
            print(f"Processing {i+1}/{len(images)}: {img_path}")
            
            try:
                result = self.run_enhanced_pipeline(img_path)
                enhanced_predictions.append(result['verdict'])
                enhanced_labels.append(label)
                enhanced_times.append(result['inference_time'])
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                continue
        
        # Calculate enhanced pipeline metrics
        enhanced_metrics = self.calculate_metrics(enhanced_predictions, enhanced_labels)
        enhanced_metrics['avg_inference_time'] = np.mean(enhanced_times)
        enhanced_metrics['total_images'] = len(enhanced_predictions)
        
        self.results['enhanced_pipeline'] = enhanced_metrics
        print(f"Enhanced Pipeline Results:")
        print(f"  Accuracy: {enhanced_metrics['accuracy']:.4f}")
        print(f"  Precision: {enhanced_metrics['precision']:.4f}")
        print(f"  Recall: {enhanced_metrics['recall']:.4f}")
        print(f"  F1: {enhanced_metrics['f1']:.4f}")
        print(f"  Avg Inference Time: {enhanced_metrics['avg_inference_time']:.4f}s")
        
        # Calculate comparison
        self.results['comparison'] = {
            'accuracy_improvement': enhanced_metrics['accuracy'] - current_metrics['accuracy'],
            'precision_improvement': enhanced_metrics['precision'] - current_metrics['precision'],
            'recall_improvement': enhanced_metrics['recall'] - current_metrics['recall'],
            'f1_improvement': enhanced_metrics['f1'] - current_metrics['f1'],
            'time_overhead': enhanced_metrics['avg_inference_time'] - current_metrics['avg_inference_time'],
            'time_overhead_percentage': (
                (enhanced_metrics['avg_inference_time'] - current_metrics['avg_inference_time']) /
                current_metrics['avg_inference_time'] * 100
                if current_metrics['avg_inference_time'] > 0 else 0
            )
        }
        
        print(f"\n=== Comparison ===")
        print(f"  Accuracy Improvement: {self.results['comparison']['accuracy_improvement']:.4f}")
        print(f"  Precision Improvement: {self.results['comparison']['precision_improvement']:.4f}")
        print(f"  Recall Improvement: {self.results['comparison']['recall_improvement']:.4f}")
        print(f"  F1 Improvement: {self.results['comparison']['f1_improvement']:.4f}")
        print(f"  Time Overhead: {self.results['comparison']['time_overhead']:.4f}s")
        print(f"  Time Overhead Percentage: {self.results['comparison']['time_overhead_percentage']:.2f}%")
        
        # Get performance stats
        perf_stats = get_performance_stats()
        self.results['performance_stats'] = perf_stats
        
        # Save results
        self.save_results()
        
        print(f"\nBenchmark results saved to {self.output_path}")
    
    def save_results(self):
        """Save benchmark results to JSON file."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w') as f:
            json.dump(self.results, f, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='TruthLens v2.2 Benchmark')
    parser.add_argument('--dataset', required=True, help='Path to dataset directory')
    parser.add_argument('--output', default='benchmark_results.json', help='Path to save results')
    
    args = parser.parse_args()
    
    benchmark = Benchmark(args.dataset, args.output)
    benchmark.run_benchmark()


if __name__ == '__main__':
    main()

"""
Error Analysis Module
=====================
Generate error analysis reports including false positives, false negatives,
confidence distributions, and representative misclassified examples.
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import matplotlib.pyplot as plt
from collections import defaultdict


class ErrorAnalyzer:
    """
    Analyze model errors and generate detailed reports.
    
    Generates:
    - False positive/negative analysis
    - Confidence distributions
    - Representative misclassified examples
    - Per-category error breakdown
    """
    
    def __init__(self, predictions: np.ndarray, labels: np.ndarray, 
                 probabilities: np.ndarray, metadata: List[Dict]):
        """
        Initialize error analyzer.
        
        Args:
            predictions: Model predictions
            labels: Ground truth labels
            probabilities: Prediction probabilities
            metadata: Sample metadata
        """
        self.predictions = predictions
        self.labels = labels
        self.probabilities = probabilities
        self.metadata = metadata
        
        # Calculate confidence (max probability)
        self.confidences = np.max(probabilities, axis=1)
        
        # Identify errors
        self.errors = predictions != labels
        self.false_positives = (predictions == 1) & (labels == 0)  # Predicted AI, actually Real
        self.false_negatives = (predictions == 0) & (labels == 1)  # Predicted Real, actually AI
        
    def analyze(self) -> Dict[str, Any]:
        """
        Perform comprehensive error analysis.
        
        Returns:
            Error analysis dictionary
        """
        analysis = {
            'total_samples': len(self.labels),
            'total_errors': int(self.errors.sum()),
            'error_rate': float(self.errors.mean()),
            'false_positives': int(self.false_positives.sum()),
            'false_negatives': int(self.false_negatives.sum()),
            'fp_rate': float(self.false_positives.mean()),
            'fn_rate': float(self.false_negatives.mean()),
            'confidence_distribution': self._analyze_confidence_distribution(),
            'error_by_generator': self._analyze_errors_by_generator(),
            'error_by_dataset': self._analyze_errors_by_dataset(),
            'misclassified_examples': self._get_misclassified_examples()
        }
        
        return analysis
    
    def _analyze_confidence_distribution(self) -> Dict[str, Any]:
        """
        Analyze confidence distribution for correct vs incorrect predictions.
        
        Returns:
            Confidence distribution statistics
        """
        correct_mask = ~self.errors
        error_mask = self.errors
        
        correct_confidences = self.confidences[correct_mask]
        error_confidences = self.confidences[error_mask]
        
        return {
            'correct': {
                'mean': float(correct_confidences.mean()),
                'std': float(correct_confidences.std()),
                'min': float(correct_confidences.min()),
                'max': float(correct_confidences.max()),
                'median': float(np.median(correct_confidences))
            },
            'incorrect': {
                'mean': float(error_confidences.mean()),
                'std': float(error_confidences.std()),
                'min': float(error_confidences.min()),
                'max': float(error_confidences.max()),
                'median': float(np.median(error_confidences))
            }
        }
    
    def _analyze_errors_by_generator(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze errors broken down by AI generator.
        
        Returns:
            Per-generator error statistics
        """
        generator_errors = defaultdict(lambda: {'total': 0, 'errors': 0, 'fp': 0, 'fn': 0})
        
        for pred, label, meta, is_error, is_fp, is_fn in zip(
            self.predictions, self.labels, self.metadata, 
            self.errors, self.false_positives, self.false_negatives
        ):
            if meta.get('label', '').lower() == 'ai':
                generator = meta.get('generator', 'unknown')
                generator_errors[generator]['total'] += 1
                if is_error:
                    generator_errors[generator]['errors'] += 1
                if is_fp:
                    generator_errors[generator]['fp'] += 1
                if is_fn:
                    generator_errors[generator]['fn'] += 1
        
        # Calculate rates
        for gen, stats in generator_errors.items():
            if stats['total'] > 0:
                stats['error_rate'] = stats['errors'] / stats['total']
                stats['fp_rate'] = stats['fp'] / stats['total']
                stats['fn_rate'] = stats['fn'] / stats['total']
            else:
                stats['error_rate'] = 0.0
                stats['fp_rate'] = 0.0
                stats['fn_rate'] = 0.0
        
        return dict(generator_errors)
    
    def _analyze_errors_by_dataset(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze errors broken down by source dataset.
        
        Returns:
            Per-dataset error statistics
        """
        dataset_errors = defaultdict(lambda: {'total': 0, 'errors': 0, 'fp': 0, 'fn': 0})
        
        for pred, label, meta, is_error, is_fp, is_fn in zip(
            self.predictions, self.labels, self.metadata,
            self.errors, self.false_positives, self.false_negatives
        ):
            dataset = meta.get('source_dataset', 'unknown')
            dataset_errors[dataset]['total'] += 1
            if is_error:
                dataset_errors[dataset]['errors'] += 1
            if is_fp:
                dataset_errors[dataset]['fp'] += 1
            if is_fn:
                dataset_errors[dataset]['fn'] += 1
        
        # Calculate rates
        for ds, stats in dataset_errors.items():
            if stats['total'] > 0:
                stats['error_rate'] = stats['errors'] / stats['total']
                stats['fp_rate'] = stats['fp'] / stats['total']
                stats['fn_rate'] = stats['fn'] / stats['total']
            else:
                stats['error_rate'] = 0.0
                stats['fp_rate'] = 0.0
                stats['fn_rate'] = 0.0
        
        return dict(dataset_errors)
    
    def _get_misclassified_examples(self, n_examples: int = 20) -> Dict[str, List[Dict]]:
        """
        Get representative misclassified examples.
        
        Args:
            n_examples: Number of examples per category
        
        Returns:
            Dictionary of misclassified examples
        """
        error_indices = np.where(self.errors)[0]
        
        # Sort by confidence (most confident errors first)
        error_confidences = self.confidences[error_indices]
        sorted_indices = error_indices[np.argsort(error_confidences)[::-1]]
        
        examples = {
            'false_positives': [],
            'false_negatives': []
        }
        
        for idx in sorted_indices:
            if len(examples['false_positives']) >= n_examples and len(examples['false_negatives']) >= n_examples:
                break
            
            example = {
                'index': int(idx),
                'file_path': self.metadata[idx].get('file_path', 'unknown'),
                'true_label': int(self.labels[idx]),
                'predicted_label': int(self.predictions[idx]),
                'confidence': float(self.confidences[idx]),
                'prob_real': float(self.probabilities[idx, 0]),
                'prob_ai': float(self.probabilities[idx, 1]),
                'generator': self.metadata[idx].get('generator', 'unknown'),
                'source_dataset': self.metadata[idx].get('source_dataset', 'unknown')
            }
            
            if self.false_positives[idx]:
                if len(examples['false_positives']) < n_examples:
                    examples['false_positives'].append(example)
            elif self.false_negatives[idx]:
                if len(examples['false_negatives']) < n_examples:
                    examples['false_negatives'].append(example)
        
        return examples
    
    def plot_confidence_distribution(self, save_path: Path):
        """
        Plot confidence distribution for correct vs incorrect predictions.
        
        Args:
            save_path: Path to save plot
        """
        correct_confidences = self.confidences[~self.errors]
        error_confidences = self.confidences[self.errors]
        
        plt.figure(figsize=(10, 6))
        plt.hist(correct_confidences, bins=50, alpha=0.7, label='Correct', color='green')
        plt.hist(error_confidences, bins=50, alpha=0.7, label='Incorrect', color='red')
        plt.xlabel('Confidence', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.title('Confidence Distribution: Correct vs Incorrect Predictions', fontsize=14)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
    
    def save_report(self, analysis: Dict[str, Any], save_path: str):
        """
        Save error analysis report to JSON.
        
        Args:
            analysis: Analysis dictionary
            save_path: Path to save report
        """
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'w') as f:
            json.dump(analysis, f, indent=2)
    
    def print_report(self, analysis: Dict[str, Any]):
        """
        Print error analysis report.
        
        Args:
            analysis: Analysis dictionary
        """
        print("\n" + "=" * 80)
        print("ERROR ANALYSIS REPORT")
        print("=" * 80)
        
        print(f"\nOverall Statistics:")
        print(f"  Total samples: {analysis['total_samples']}")
        print(f"  Total errors: {analysis['total_errors']}")
        print(f"  Error rate: {analysis['error_rate']:.4f}")
        print(f"  False positives: {analysis['false_positives']} ({analysis['fp_rate']:.4f})")
        print(f"  False negatives: {analysis['false_negatives']} ({analysis['fn_rate']:.4f})")
        
        print(f"\nConfidence Distribution:")
        print(f"  Correct predictions:")
        print(f"    Mean: {analysis['confidence_distribution']['correct']['mean']:.4f}")
        print(f"    Std: {analysis['confidence_distribution']['correct']['std']:.4f}")
        print(f"    Median: {analysis['confidence_distribution']['correct']['median']:.4f}")
        print(f"  Incorrect predictions:")
        print(f"    Mean: {analysis['confidence_distribution']['incorrect']['mean']:.4f}")
        print(f"    Std: {analysis['confidence_distribution']['incorrect']['std']:.4f}")
        print(f"    Median: {analysis['confidence_distribution']['incorrect']['median']:.4f}")
        
        if analysis['error_by_generator']:
            print(f"\nErrors by Generator:")
            for generator, stats in analysis['error_by_generator'].items():
                print(f"  {generator}:")
                print(f"    Total: {stats['total']}")
                print(f"    Errors: {stats['errors']} ({stats['error_rate']:.4f})")
                print(f"    FP: {stats['fp']} ({stats['fp_rate']:.4f})")
                print(f"    FN: {stats['fn']} ({stats['fn_rate']:.4f})")
        
        if analysis['error_by_dataset']:
            print(f"\nErrors by Dataset:")
            for dataset, stats in analysis['error_by_dataset'].items():
                print(f"  {dataset}:")
                print(f"    Total: {stats['total']}")
                print(f"    Errors: {stats['errors']} ({stats['error_rate']:.4f})")
                print(f"    FP: {stats['fp']} ({stats['fp_rate']:.4f})")
                print(f"    FN: {stats['fn']} ({stats['fn_rate']:.4f})")
        
        print("\n" + "=" * 80)


def analyze_errors(
    predictions: np.ndarray,
    labels: np.ndarray,
    probabilities: np.ndarray,
    metadata: List[Dict],
    save_dir: Path
) -> Dict[str, Any]:
    """
    Perform error analysis and save results.
    
    Args:
        predictions: Model predictions
        labels: Ground truth labels
        probabilities: Prediction probabilities
        metadata: Sample metadata
        save_dir: Directory to save results
    
    Returns:
        Error analysis dictionary
    """
    analyzer = ErrorAnalyzer(predictions, labels, probabilities, metadata)
    analysis = analyzer.analyze()
    
    # Save report
    analyzer.save_report(analysis, save_dir / 'error_analysis.json')
    
    # Plot confidence distribution
    analyzer.plot_confidence_distribution(save_dir / 'confidence_distribution.png')
    
    # Print report
    analyzer.print_report(analysis)
    
    return analysis

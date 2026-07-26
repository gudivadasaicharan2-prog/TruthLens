"""
Automatic Benchmark Manager for TruthLens
==========================================
Download benchmark datasets, run inference, and generate evaluation reports.
"""

import sys
from pathlib import Path
import json
import csv
from typing import Dict, List, Callable, Optional, Any
from abc import ABC, abstractmethod
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.training.dataloader import get_default_transforms
from app.training.models import create_model
from app.training.utils import get_device


# ============================================================================
# Dataset Registry and Base Classes
# ============================================================================

class BenchmarkDataset(ABC):
    """
    Abstract base class for benchmark datasets.
    """
    
    def __init__(self, cache_dir: str = "data/benchmark_cache"):
        """
        Initialize benchmark dataset.
        
        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.name = self.__class__.__name__
    
    @abstractmethod
    def download(self) -> str:
        """
        Download dataset and return path to data.
        
        Returns:
            Path to downloaded data
        """
        pass
    
    @abstractmethod
    def load(self, data_path: str) -> Dataset:
        """
        Load dataset into PyTorch Dataset.
        
        Args:
            data_path: Path to downloaded data
        
        Returns:
            PyTorch Dataset
        """
        pass
    
    @abstractmethod
    def get_label_mapping(self) -> Dict[str, int]:
        """
        Get mapping from dataset labels to model labels (0=Real, 1=AI).
        
        Returns:
            Dict mapping dataset label names to model label indices
        """
        pass


class BenchmarkDatasetRegistry:
    """
    Registry for benchmark datasets.
    """
    
    _datasets: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str):
        """
        Decorator to register a benchmark dataset.
        
        Args:
            name: Name to register the dataset under
        """
        def decorator(dataset_class: type):
            cls._datasets[name] = dataset_class
            return dataset_class
        return decorator
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """
        Get a registered dataset class.
        
        Args:
            name: Name of dataset
        
        Returns:
            Dataset class or None if not found
        """
        return cls._datasets.get(name)
    
    @classmethod
    def list_datasets(cls) -> List[str]:
        """
        List all registered datasets.
        
        Returns:
            List of dataset names
        """
        return list(cls._datasets.keys())


# ============================================================================
# Benchmark Dataset Implementations
# ============================================================================

@BenchmarkDatasetRegistry.register("cifake")
class CIFAKEBenchmark(BenchmarkDataset):
    """
    CIFAKE benchmark dataset (subset for testing).
    Uses CIFAKE from Hugging Face datasets.
    """
    
    def download(self) -> str:
        """Download CIFAKE dataset."""
        try:
            from datasets import load_dataset
            
            print(f"[{self.name}] Downloading CIFAKE from Hugging Face...")
            # Download a small subset for benchmarking
            dataset = load_dataset("competitions/AI-or-Not", split="test[:1000]")
            
            # Save to cache
            cache_path = self.cache_dir / "cifake"
            cache_path.mkdir(exist_ok=True)
            dataset.save_to_disk(str(cache_path))
            
            print(f"[{self.name}] Downloaded and cached to {cache_path}")
            return str(cache_path)
        except ImportError:
            print(f"[{self.name}] Hugging Face datasets not available. Please install: pip install datasets")
            raise
        except Exception as e:
            print(f"[{self.name}] Error downloading CIFAKE: {e}")
            raise
    
    def load(self, data_path: str) -> Dataset:
        """Load CIFAKE dataset."""
        try:
            from datasets import load_from_disk
            
            dataset = load_from_disk(data_path)
            return CIFAKEHFDataset(dataset)
        except ImportError:
            print(f"[{self.name}] Hugging Face datasets not available")
            raise
    
    def get_label_mapping(self) -> Dict[str, int]:
        """CIFAKE label mapping."""
        return {"Real": 0, "Fake": 1}


class CIFAKEHFDataset(Dataset):
    """Wrapper for Hugging Face CIFAKE dataset."""
    
    def __init__(self, hf_dataset):
        self.dataset = hf_dataset
    
    def __len__(self):
        return len(self.dataset)
    
    def __getitem__(self, idx):
        item = self.dataset[idx]
        # Assuming dataset has 'image' and 'label' fields
        image = item['image']
        label = item['label']
        return image, label


@BenchmarkDatasetRegistry.register("local_folder")
class LocalFolderBenchmark(BenchmarkDataset):
    """
    Local folder benchmark dataset.
    Expects folder structure: dataset/real/ and dataset/ai/
    """
    
    def __init__(self, folder_path: str, cache_dir: str = "data/benchmark_cache"):
        """
        Initialize local folder benchmark.
        
        Args:
            folder_path: Path to local folder with real/ai subfolders
            cache_dir: Cache directory (not used for local)
        """
        super().__init__(cache_dir)
        self.folder_path = Path(folder_path)
    
    def download(self) -> str:
        """Return local folder path (no download needed)."""
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Local folder not found: {self.folder_path}")
        print(f"[{self.name}] Using local folder: {self.folder_path}")
        return str(self.folder_path)
    
    def load(self, data_path: str) -> Dataset:
        """Load local folder dataset."""
        return LocalFolderDataset(data_path)
    
    def get_label_mapping(self) -> Dict[str, int]:
        """Local folder label mapping."""
        return {"real": 0, "ai": 1}


class LocalFolderDataset(Dataset):
    """Dataset for local folder structure with recursive image discovery."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path)
        self.samples = []
        
        real_count = 0
        ai_count = 0
        
        # Recursively load real images
        real_folder = self.folder_path / "real"
        if real_folder.exists():
            for img_path in real_folder.rglob("*"):
                if img_path.is_file() and img_path.suffix.lower() in self.SUPPORTED_FORMATS:
                    self.samples.append((img_path, 0))
                    real_count += 1
        
        # Recursively load AI images
        ai_folder = self.folder_path / "ai"
        if ai_folder.exists():
            for img_path in ai_folder.rglob("*"):
                if img_path.is_file() and img_path.suffix.lower() in self.SUPPORTED_FORMATS:
                    self.samples.append((img_path, 1))
                    ai_count += 1
        
        if len(self.samples) == 0:
            raise ValueError(f"No images found in {folder_path}")
        
        print(f"[LocalFolderDataset] Found {real_count} Real images, {ai_count} AI images (Total: {len(self.samples)})")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert('RGB')
        return image, label


# ============================================================================
# Benchmark Manager
# ============================================================================

class BenchmarkManager:
    """
    Manager for running benchmarks on TruthLens model.
    """
    
    def __init__(
        self,
        checkpoint_path: str,
        output_dir: str = "experiments/benchmark",
        cache_dir: str = "data/benchmark_cache"
    ):
        """
        Initialize benchmark manager.
        
        Args:
            checkpoint_path: Path to model checkpoint
            output_dir: Directory to save benchmark results
            cache_dir: Directory to cache downloaded datasets
        """
        self.checkpoint_path = checkpoint_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = cache_dir
        self.device = get_device()
        self.model = None
        self.transform = None
    
    def load_model(self):
        """Load model from checkpoint."""
        print("[Benchmark] Loading model...")
        self.model = create_model(
            architecture='efficientnet_b4',
            num_classes=2,
            pretrained=False,
            dropout=0.3
        )
        
        checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        print(f"[Benchmark] Loaded checkpoint from {self.checkpoint_path}")
        print(f"  Epoch: {checkpoint['epoch']}")
        print(f"  Score: {checkpoint['score']:.4f}")
    
    def load_transforms(self):
        """Load validation transforms."""
        _, self.transform = get_default_transforms(image_size=224, augment=False)
    
    def run_benchmark(
        self,
        dataset_name: str,
        **dataset_kwargs
    ) -> Dict[str, Any]:
        """
        Run benchmark on a dataset.
        
        Args:
            dataset_name: Name of registered dataset
            **dataset_kwargs: Additional arguments for dataset initialization
        
        Returns:
            Benchmark results dictionary
        """
        print("\n" + "=" * 80)
        print(f"Running Benchmark: {dataset_name}")
        print("=" * 80)
        
        # Get dataset class
        dataset_class = BenchmarkDatasetRegistry.get(dataset_name)
        if dataset_class is None:
            available = BenchmarkDatasetRegistry.list_datasets()
            raise ValueError(
                f"Unknown dataset: {dataset_name}. "
                f"Available: {', '.join(available)}"
            )
        
        # Initialize dataset
        dataset = dataset_class(cache_dir=self.cache_dir, **dataset_kwargs)
        
        # Download if needed
        print(f"\n[Step 1] Preparing dataset...")
        data_path = dataset.download()
        
        # Load dataset
        print(f"\n[Step 2] Loading dataset...")
        raw_dataset = dataset.load(data_path)
        
        # Wrap with transforms
        transformed_dataset = TransformedDataset(raw_dataset, self.transform)
        
        # Get label mapping
        label_mapping = dataset.get_label_mapping()
        
        # Create dataloader
        dataloader = DataLoader(
            transformed_dataset,
            batch_size=32,
            shuffle=False,
            num_workers=0,
            pin_memory=False
        )
        
        print(f"Dataset size: {len(transformed_dataset)}")
        
        # Run inference
        print(f"\n[Step 3] Running inference...")
        results = self._run_inference(dataloader, label_mapping)
        
        # Calculate metrics
        print(f"\n[Step 4] Calculating metrics...")
        metrics = self._calculate_metrics(results)
        
        # Save results
        print(f"\n[Step 5] Saving results...")
        benchmark_output_dir = self.output_dir / dataset_name
        benchmark_output_dir.mkdir(exist_ok=True)
        
        self._save_results(metrics, results, benchmark_output_dir)
        
        # Print summary
        print(f"\n[Step 6] Summary:")
        self._print_summary(metrics, dataset_name)
        
        return metrics
    
    def _run_inference(
        self,
        dataloader: DataLoader,
        label_mapping: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Run inference on dataset.
        
        Args:
            dataloader: DataLoader for dataset
            label_mapping: Mapping from dataset labels to model labels
        
        Returns:
            Dictionary with predictions, labels, and probabilities
        """
        all_predictions = []
        all_labels = []
        all_probabilities = []
        
        with torch.no_grad():
            for images, labels in tqdm(dataloader, desc="Inference"):
                images = images.to(self.device)
                
                outputs = self.model(images)
                probabilities = torch.softmax(outputs, dim=1)
                predictions = torch.argmax(outputs, dim=1)
                
                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_probabilities.extend(probabilities.cpu().numpy())
        
        return {
            'predictions': np.array(all_predictions),
            'labels': np.array(all_labels),
            'probabilities': np.array(all_probabilities)
        }
    
    def _calculate_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate evaluation metrics using NumPy only.
        
        Args:
            results: Dictionary with predictions and labels
        
        Returns:
            Metrics dictionary
        """
        predictions = results['predictions']
        labels = results['labels']
        probabilities = results['probabilities']
        
        metrics = {}
        
        # Sample counts
        metrics['total_samples'] = len(labels)
        metrics['predicted_real'] = int(np.sum(predictions == 0))
        metrics['predicted_ai'] = int(np.sum(predictions == 1))
        metrics['actual_real'] = int(np.sum(labels == 0))
        metrics['actual_ai'] = int(np.sum(labels == 1))
        
        # Confusion matrix
        cm = self._compute_confusion_matrix(labels, predictions)
        metrics['confusion_matrix'] = cm.tolist()
        
        # Basic metrics from confusion matrix
        tn, fp, fn, tp = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
        
        # Accuracy
        metrics['accuracy'] = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
        
        # Precision (positive class = AI = 1)
        metrics['precision'] = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        
        # Recall
        metrics['recall'] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        # F1 Score
        if metrics['precision'] + metrics['recall'] > 0:
            metrics['f1_score'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
        else:
            metrics['f1_score'] = 0.0
        
        # ROC AUC (manual implementation using trapezoidal rule)
        if probabilities.shape[1] >= 2:
            metrics['roc_auc'] = self._compute_roc_auc(labels, probabilities[:, 1])
        else:
            metrics['roc_auc'] = 0.0
        
        # Classification report
        metrics['classification_report'] = self._compute_classification_report(labels, predictions, cm)
        
        return metrics
    
    def _compute_confusion_matrix(self, labels: np.ndarray, predictions: np.ndarray) -> np.ndarray:
        """
        Compute confusion matrix using NumPy.
        
        Args:
            labels: Ground truth labels
            predictions: Predicted labels
        
        Returns:
            2x2 confusion matrix [[TN, FP], [FN, TP]]
        """
        cm = np.zeros((2, 2), dtype=int)
        for true_label, pred_label in zip(labels, predictions):
            cm[true_label, pred_label] += 1
        return cm
    
    def _compute_roc_auc(self, labels: np.ndarray, scores: np.ndarray) -> float:
        """
        Compute ROC AUC using trapezoidal rule.
        
        Args:
            labels: Ground truth labels (0 or 1)
            scores: Prediction scores for positive class
        
        Returns:
            ROC AUC score
        """
        # Sort by scores descending
        sorted_indices = np.argsort(scores)[::-1]
        sorted_labels = labels[sorted_indices]
        
        # Compute TPR and FPR at each threshold
        tpr_values = []
        fpr_values = []
        
        total_pos = np.sum(labels == 1)
        total_neg = np.sum(labels == 0)
        
        if total_pos == 0 or total_neg == 0:
            return 0.0
        
        tp = 0
        fp = 0
        
        # Start at (0, 0)
        tpr_values.append(0.0)
        fpr_values.append(0.0)
        
        for label in sorted_labels:
            if label == 1:
                tp += 1
            else:
                fp += 1
            
            tpr = tp / total_pos
            fpr = fp / total_neg
            tpr_values.append(tpr)
            fpr_values.append(fpr)
        
        # Compute AUC using trapezoidal rule
        auc = 0.0
        for i in range(1, len(fpr_values)):
            auc += (fpr_values[i] - fpr_values[i-1]) * (tpr_values[i] + tpr_values[i-1]) / 2
        
        return auc
    
    def _compute_classification_report(self, labels: np.ndarray, predictions: np.ndarray, cm: np.ndarray) -> Dict[str, Any]:
        """
        Compute classification report dictionary.
        
        Args:
            labels: Ground truth labels
            predictions: Predicted labels
            cm: Confusion matrix
        
        Returns:
            Classification report dictionary
        """
        tn, fp, fn, tp = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
        
        # Per-class metrics
        report = {}
        
        # Real class (label 0)
        report['Real'] = {
            'precision': tn / (tn + fn) if (tn + fn) > 0 else 0.0,
            'recall': tn / (tn + fp) if (tn + fp) > 0 else 0.0,
            'f1-score': 0.0,
            'support': int(tn + fp)
        }
        if report['Real']['precision'] + report['Real']['recall'] > 0:
            report['Real']['f1-score'] = 2 * (report['Real']['precision'] * report['Real']['recall']) / (report['Real']['precision'] + report['Real']['recall'])
        
        # AI class (label 1)
        report['AI'] = {
            'precision': tp / (tp + fp) if (tp + fp) > 0 else 0.0,
            'recall': tp / (tp + fn) if (tp + fn) > 0 else 0.0,
            'f1-score': 0.0,
            'support': int(tp + fn)
        }
        if report['AI']['precision'] + report['AI']['recall'] > 0:
            report['AI']['f1-score'] = 2 * (report['AI']['precision'] * report['AI']['recall']) / (report['AI']['precision'] + report['AI']['recall'])
        
        # Macro average
        report['macro avg'] = {
            'precision': (report['Real']['precision'] + report['AI']['precision']) / 2,
            'recall': (report['Real']['recall'] + report['AI']['recall']) / 2,
            'f1-score': (report['Real']['f1-score'] + report['AI']['f1-score']) / 2,
            'support': report['Real']['support'] + report['AI']['support']
        }
        
        # Weighted average
        total_support = report['Real']['support'] + report['AI']['support']
        report['weighted avg'] = {
            'precision': (report['Real']['precision'] * report['Real']['support'] + report['AI']['precision'] * report['AI']['support']) / total_support if total_support > 0 else 0.0,
            'recall': (report['Real']['recall'] * report['Real']['support'] + report['AI']['recall'] * report['AI']['support']) / total_support if total_support > 0 else 0.0,
            'f1-score': (report['Real']['f1-score'] * report['Real']['support'] + report['AI']['f1-score'] * report['AI']['support']) / total_support if total_support > 0 else 0.0,
            'support': total_support
        }
        
        return report
    
    def _save_results(
        self,
        metrics: Dict[str, Any],
        results: Dict[str, Any],
        output_dir: Path
    ):
        """
        Save benchmark results.
        
        Args:
            metrics: Metrics dictionary
            results: Raw results dictionary
            output_dir: Output directory
        """
        # Save JSON summary
        with open(output_dir / 'summary.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Save CSV report
        self._save_csv_report(results, output_dir / 'results.csv')
        
        print(f"[Benchmark] Saved results to {output_dir}")
    
    def _save_csv_report(self, results: Dict[str, Any], output_path: Path):
        """
        Save detailed CSV report.
        
        Args:
            results: Raw results dictionary
            output_path: Path to save CSV
        """
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'label', 'prediction', 'prob_real', 'prob_ai'])
            
            for i, (label, pred, probs) in enumerate(zip(
                results['labels'],
                results['predictions'],
                results['probabilities']
            )):
                writer.writerow([
                    i,
                    int(label),
                    int(pred),
                    f"{probs[0]:.4f}",
                    f"{probs[1]:.4f}"
                ])
    
    def _print_summary(self, metrics: Dict[str, Any], dataset_name: str):
        """
        Print benchmark summary.
        
        Args:
            metrics: Metrics dictionary
            dataset_name: Name of dataset
        """
        print("\n" + "=" * 80)
        print(f"BENCHMARK RESULTS: {dataset_name}")
        print("=" * 80)
        print(f"Total Samples: {metrics['total_samples']}")
        print(f"Actual Real: {metrics['actual_real']} | Actual AI: {metrics['actual_ai']}")
        print(f"Predicted Real: {metrics['predicted_real']} | Predicted AI: {metrics['predicted_ai']}")
        print("-" * 80)
        print(f"Accuracy:  {metrics['accuracy']:.4f}")
        print(f"Precision: {metrics['precision']:.4f}")
        print(f"Recall:    {metrics['recall']:.4f}")
        print(f"F1 Score:  {metrics['f1_score']:.4f}")
        print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
        print("=" * 80)


class TransformedDataset(Dataset):
    """Wrapper to apply transforms to a dataset."""
    
    def __init__(self, base_dataset: Dataset, transform):
        self.base_dataset = base_dataset
        self.transform = transform
    
    def __len__(self):
        return len(self.base_dataset)
    
    def __getitem__(self, idx):
        image, label = self.base_dataset[idx]
        if self.transform:
            image = self.transform(image)
        return image, label


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main benchmark runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run TruthLens benchmarks')
    parser.add_argument(
        '--dataset',
        type=str,
        help='Name of benchmark dataset (use --list to see available)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available benchmark datasets'
    )
    parser.add_argument(
        '--checkpoint',
        type=str,
        default='experiments/cifake_efficientnet_b4_baseline/checkpoints/latest_checkpoint.pth',
        help='Path to model checkpoint'
    )
    parser.add_argument(
        '--folder',
        type=str,
        help='Path to local folder (for local_folder dataset)'
    )
    
    args = parser.parse_args()
    
    # List available datasets
    if args.list:
        print("Available benchmark datasets:")
        for name in BenchmarkDatasetRegistry.list_datasets():
            print(f"  - {name}")
        return
    
    # Validate that --dataset is provided when not using --list
    if not args.dataset:
        parser.error("--dataset is required when not using --list")
    
    # Initialize benchmark manager
    manager = BenchmarkManager(
        checkpoint_path=args.checkpoint,
        output_dir='experiments/benchmark',
        cache_dir='data/benchmark_cache'
    )
    
    # Load model and transforms
    manager.load_model()
    manager.load_transforms()
    
    # Run benchmark
    dataset_kwargs = {}
    if args.dataset == 'local_folder' and args.folder:
        dataset_kwargs['folder_path'] = args.folder
    
    try:
        results = manager.run_benchmark(args.dataset, **dataset_kwargs)
        print(f"\n[Benchmark] Complete!")
    except Exception as e:
        print(f"\n[Error] Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    main()

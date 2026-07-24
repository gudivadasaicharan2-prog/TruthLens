"""
Benchmark Builder
=================
Builds benchmark datasets from TruthLensDataset for model evaluation.
"""

from pathlib import Path
from typing import Dict, List, Optional
import csv
import random
from collections import defaultdict


class BenchmarkBuilder:
    """Build benchmark datasets for model evaluation."""
    
    def __init__(self, dataset_dir: str = "TruthLensDataset", output_dir: str = "benchmark"):
        """
        Initialize benchmark builder.
        
        Args:
            dataset_dir: TruthLensDataset directory
            output_dir: Output directory for benchmark datasets
        """
        self.dataset_dir = Path(dataset_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_benchmark(self, categories: List[str] = None, 
                       samples_per_category: int = 100,
                       split_ratio: float = 0.8) -> Dict[str, any]:
        """
        Build benchmark dataset with balanced categories.
        
        Args:
            categories: List of categories to include (None for all)
            samples_per_category: Number of samples per category
            split_ratio: Train/validation split ratio
        
        Returns:
            Dict with benchmark statistics
        """
        print("[BenchmarkBuilder] Building benchmark dataset...")
        
        # Define default categories
        if categories is None:
            categories = [
                "real_portrait",
                "real_landscape", 
                "real_object",
                "real_document",
                "real_screenshot",
                "ai_midjourney",
                "ai_sdxl",
                "ai_adm",
                "ai_glide"
            ]
        
        # Collect samples
        samples = self._collect_samples(categories, samples_per_category)
        
        # Split into train/val
        train_samples, val_samples = self._split_samples(samples, split_ratio)
        
        # Save benchmark files
        train_csv = self._save_benchmark_csv(train_samples, "train")
        val_csv = self._save_benchmark_csv(val_samples, "val")
        
        # Copy files to benchmark directory
        train_dir = self.output_dir / "train"
        val_dir = self.output_dir / "val"
        
        train_dir.mkdir(exist_ok=True)
        val_dir.mkdir(exist_ok=True)
        
        self._copy_samples(train_samples, train_dir)
        self._copy_samples(val_samples, val_dir)
        
        stats = {
            "categories": categories,
            "samples_per_category": samples_per_category,
            "split_ratio": split_ratio,
            "total_train_samples": len(train_samples),
            "total_val_samples": len(val_samples),
            "train_csv": str(train_csv),
            "val_csv": str(val_csv),
            "train_dir": str(train_dir),
            "val_dir": str(val_dir)
        }
        
        print(f"[BenchmarkBuilder] Benchmark built: {len(train_samples)} train, {len(val_samples)} val")
        return stats
    
    def _collect_samples(self, categories: List[str], samples_per_category: int) -> List[Dict]:
        """
        Collect samples from dataset.
        
        Args:
            categories: List of categories
            samples_per_category: Samples per category
        
        Returns:
            List of sample dicts
        """
        samples = []
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        for category in categories:
            # Parse category
            if category.startswith("real_"):
                content_type = "real"
                subcategory = category.replace("real_", "")
                source_dir = self.dataset_dir / "images" / "real" / subcategory
            elif category.startswith("ai_"):
                content_type = "ai"
                generator = category.replace("ai_", "")
                source_dir = self.dataset_dir / "images" / "ai" / generator
            else:
                print(f"[BenchmarkBuilder] Unknown category format: {category}")
                continue
            
            if not source_dir.exists():
                print(f"[BenchmarkBuilder] Category directory not found: {source_dir}")
                continue
            
            # Collect images
            image_files = list(source_dir.glob("*"))
            image_files = [f for f in image_files if f.suffix.lower() in image_extensions]
            
            # Random sample
            if len(image_files) > samples_per_category:
                image_files = random.sample(image_files, samples_per_category)
            
            for image_path in image_files:
                samples.append({
                    "filename": image_path.name,
                    "filepath": str(image_path),
                    "category": category,
                    "content_type": content_type,
                    "label": content_type
                })
        
        return samples
    
    def _split_samples(self, samples: List[Dict], split_ratio: float) -> tuple:
        """
        Split samples into train and validation sets.
        
        Args:
            samples: List of samples
            split_ratio: Train split ratio
        
        Returns:
            Tuple of (train_samples, val_samples)
        """
        random.shuffle(samples)
        split_idx = int(len(samples) * split_ratio)
        return samples[:split_idx], samples[split_idx:]
    
    def _save_benchmark_csv(self, samples: List[Dict], split: str) -> Path:
        """
        Save benchmark CSV file.
        
        Args:
            samples: List of samples
            split: "train" or "val"
        
        Returns:
            Path to CSV file
        """
        csv_path = self.output_dir / f"{split}.csv"
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'filepath', 'category', 'content_type', 'label'])
            
            for sample in samples:
                writer.writerow([
                    sample['filename'],
                    sample['filepath'],
                    sample['category'],
                    sample['content_type'],
                    sample['label']
                ])
        
        print(f"[BenchmarkBuilder] Saved {split}.csv with {len(samples)} samples")
        return csv_path
    
    def _copy_samples(self, samples: List[Dict], output_dir: Path) -> None:
        """
        Copy sample files to output directory.
        
        Args:
            samples: List of samples
            output_dir: Output directory
        """
        import shutil
        
        for sample in samples:
            src = Path(sample['filepath'])
            dst = output_dir / sample['category'] / sample['filename']
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"[BenchmarkBuilder] Error copying {src}: {e}")
    
    def build_category_benchmark(self, category: str, samples: int = 100) -> Dict[str, any]:
        """
        Build benchmark for a single category.
        
        Args:
            category: Category name
            samples: Number of samples
        
        Returns:
            Dict with benchmark statistics
        """
        return self.build_benchmark(categories=[category], samples_per_category=samples)
    
    def get_category_distribution(self) -> Dict[str, int]:
        """
        Get distribution of samples by category.
        
        Returns:
            Dict mapping category to count
        """
        distribution = defaultdict(int)
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        
        images_dir = self.dataset_dir / "images"
        if images_dir.exists():
            for content_type in ["real", "ai"]:
                content_dir = images_dir / content_type
                if content_dir.exists():
                    for subcategory in content_dir.iterdir():
                        if subcategory.is_dir():
                            category_name = f"{content_type}_{subcategory.name}"
                            count = len([f for f in subcategory.glob("*") if f.suffix.lower() in image_extensions])
                            distribution[category_name] = count
        
        return dict(distribution)

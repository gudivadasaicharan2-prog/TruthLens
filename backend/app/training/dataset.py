"""
TruthLens Dataset
=================
PyTorch Dataset class for AI content detection using metadata.csv.
"""

import csv
from pathlib import Path
from typing import Optional, List, Dict, Callable, Tuple
from PIL import Image
import torch
from torch.utils.data import Dataset


class TruthLensDataset(Dataset):
    """
    PyTorch Dataset for TruthLens AI content detection.
    
    Reads metadata.csv for efficient dataset loading with filtering capabilities.
    """
    
    def __init__(
        self,
        metadata_path: str,
        dataset_dir: str,
        split: Optional[str] = None,
        label: Optional[str] = None,
        generator: Optional[str] = None,
        source_dataset: Optional[str] = None,
        transform: Optional[Callable] = None
    ):
        """
        Initialize TruthLens Dataset.
        
        Args:
            metadata_path: Path to metadata.csv file
            dataset_dir: Base directory containing images (TruthLensDataset)
            split: Filter by split ('train' or 'val')
            label: Filter by label ('real' or 'ai')
            generator: Filter by generator name (for AI images)
            source_dataset: Filter by source dataset
            transform: Optional transform to apply to images
        """
        self.metadata_path = Path(metadata_path)
        self.dataset_dir = Path(dataset_dir)
        self.transform = transform
        
        # Load and filter metadata
        self.samples = self._load_and_filter_metadata(
            split=split,
            label=label,
            generator=generator,
            source_dataset=source_dataset
        )
        
        print(f"[TruthLensDataset] Loaded {len(self.samples)} samples")
        if split:
            print(f"  Split: {split}")
        if label:
            print(f"  Label: {label}")
        if generator:
            print(f"  Generator: {generator}")
        if source_dataset:
            print(f"  Source: {source_dataset}")
    
    def _load_and_filter_metadata(
        self,
        split: Optional[str] = None,
        label: Optional[str] = None,
        generator: Optional[str] = None,
        source_dataset: Optional[str] = None
    ) -> List[Dict]:
        """
        Load and filter metadata from CSV file.
        
        Args:
            split: Filter by split
            label: Filter by label
            generator: Filter by generator
            source_dataset: Filter by source dataset
        
        Returns:
            List of filtered sample dictionaries
        """
        samples = []
        
        if not self.metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_path}")
        
        with open(self.metadata_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Apply filters
                if split and row.get('split', '').lower() != split.lower():
                    continue
                if label and row.get('label', '').lower() != label.lower():
                    continue
                if generator and row.get('generator', '').lower() != generator.lower():
                    continue
                if source_dataset and row.get('source_dataset', '').lower() != source_dataset.lower():
                    continue
                
                samples.append(row)
        
        return samples
    
    def __len__(self) -> int:
        """Return the number of samples in the dataset."""
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, Dict]:
        """
        Get a sample from the dataset.
        
        Args:
            idx: Index of the sample
        
        Returns:
            Tuple of (image_tensor, label, metadata_dict)
        """
        sample = self.samples[idx]
        
        # Load image
        image_path = self.dataset_dir / sample['file_path']
        image = Image.open(image_path).convert('RGB')
        
        # Apply transform
        if self.transform:
            image = self.transform(image)
        
        # Convert label to integer (0 for real, 1 for ai)
        label_int = 0 if sample['label'].lower() == 'real' else 1
        
        # Return image, label, and metadata
        return image, label_int, sample
    
    def get_label_counts(self) -> Dict[str, int]:
        """
        Get count of samples per label.
        
        Returns:
            Dict mapping label to count
        """
        counts = {"real": 0, "ai": 0}
        for sample in self.samples:
            label = sample['label'].lower()
            if label in counts:
                counts[label] += 1
        return counts
    
    def get_generator_counts(self) -> Dict[str, int]:
        """
        Get count of samples per generator (for AI images).
        
        Returns:
            Dict mapping generator to count
        """
        counts = {}
        for sample in self.samples:
            if sample['label'].lower() == 'ai':
                generator = sample.get('generator', 'unknown')
                counts[generator] = counts.get(generator, 0) + 1
        return counts
    
    def get_split_counts(self) -> Dict[str, int]:
        """
        Get count of samples per split.
        
        Returns:
            Dict mapping split to count
        """
        counts = {}
        for sample in self.samples:
            split = sample.get('split', 'unknown')
            counts[split] = counts.get(split, 0) + 1
        return counts

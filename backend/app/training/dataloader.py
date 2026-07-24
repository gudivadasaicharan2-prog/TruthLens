"""
TruthLens DataLoader
====================
Configurable DataLoader system with balanced sampling.
"""

from typing import Optional, Dict, List, Callable
import torch
from torch.utils.data import DataLoader, Sampler
from torch.utils.data.distributed import DistributedSampler
import numpy as np
from collections import defaultdict

from .dataset import TruthLensDataset


class BalancedGeneratorSampler(Sampler):
    """
    Sampler that ensures balanced sampling across AI generators.
    
    Each generator contributes equally to the training process,
    preventing bias toward generators with more samples.
    """
    
    def __init__(
        self,
        dataset: TruthLensDataset,
        generator_counts: Dict[str, int],
        samples_per_generator: Optional[int] = None
    ):
        """
        Initialize balanced generator sampler.
        
        Args:
            dataset: TruthLensDataset instance
            generator_counts: Dict mapping generator to sample count
            samples_per_generator: Number of samples per generator per epoch
                                   (None = use minimum count)
        """
        self.dataset = dataset
        self.generator_counts = generator_counts
        
        # Group indices by generator
        self.generator_indices = defaultdict(list)
        for idx, sample in enumerate(dataset.samples):
            if sample['label'].lower() == 'ai':
                generator = sample.get('generator', 'unknown')
                self.generator_indices[generator].append(idx)
        
        # Determine samples per generator
        if samples_per_generator is None:
            self.samples_per_generator = min(len(indices) for indices in self.generator_indices.values())
        else:
            self.samples_per_generator = samples_per_generator
        
        # Calculate total size
        self.num_generators = len(self.generator_indices)
        self.total_size = self.samples_per_generator * self.num_generators
        
        print(f"[BalancedGeneratorSampler] {self.num_generators} generators")
        print(f"  Samples per generator: {self.samples_per_generator}")
        print(f"  Total samples per epoch: {self.total_size}")
    
    def __iter__(self):
        """Generate balanced indices."""
        indices = []
        
        for generator in self.generator_indices.keys():
            gen_indices = self.generator_indices[generator]
            # Sample with replacement if needed
            if len(gen_indices) >= self.samples_per_generator:
                sampled = np.random.choice(gen_indices, self.samples_per_generator, replace=False)
            else:
                sampled = np.random.choice(gen_indices, self.samples_per_generator, replace=True)
            indices.extend(sampled)
        
        # Shuffle the combined indices
        np.random.shuffle(indices)
        return iter(indices)
    
    def __len__(self) -> int:
        """Return the total number of samples."""
        return self.total_size


def create_data_loaders(
    train_metadata: str,
    val_metadata: str,
    dataset_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    pin_memory: bool = True,
    train_transform: Optional[Callable] = None,
    val_transform: Optional[Callable] = None,
    balanced_sampling: bool = True,
    samples_per_generator: Optional[int] = None,
    deterministic: bool = False
) -> Dict[str, DataLoader]:
    """
    Create train and validation data loaders.
    
    Args:
        train_metadata: Path to training metadata.csv
        val_metadata: Path to validation metadata.csv
        dataset_dir: Base directory containing images
        batch_size: Batch size for data loaders
        num_workers: Number of worker processes for data loading
        pin_memory: Whether to pin memory for faster GPU transfer
        train_transform: Transform to apply to training images
        val_transform: Transform to apply to validation images
        balanced_sampling: Whether to use balanced generator sampling
        samples_per_generator: Samples per generator for balanced sampling
        deterministic: Whether to use deterministic training (fixed seed)
    
    Returns:
        Dict containing 'train' and 'val' DataLoaders
    """
    # Set seed for deterministic training
    if deterministic:
        torch.manual_seed(42)
        np.random.seed(42)
    
    # Create datasets
    train_dataset = TruthLensDataset(
        metadata_path=train_metadata,
        dataset_dir=dataset_dir,
        split='train',
        transform=train_transform
    )
    
    val_dataset = TruthLensDataset(
        metadata_path=val_metadata,
        dataset_dir=dataset_dir,
        split='val',
        transform=val_transform
    )
    
    # Create samplers
    train_sampler = None
    val_sampler = None
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        sampler=train_sampler,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=True if num_workers > 0 else False,
        prefetch_factor=2 if num_workers > 0 else None,
        drop_last=False
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        sampler=val_sampler,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=True if num_workers > 0 else False,
        prefetch_factor=2 if num_workers > 0 else None,
        drop_last=False
    )
    
    print(f"[DataLoader] Train batches: {len(train_loader)}")
    print(f"[DataLoader] Val batches: {len(val_loader)}")
    
    return {
        'train': train_loader,
        'val': val_loader,
        'train_dataset': train_dataset,
        'val_dataset': val_dataset
    }


def get_default_transforms(image_size: int = 224, augment: bool = True):
    """
    Get default image transforms for training and validation.
    
    Args:
        image_size: Target image size
        augment: Whether to apply data augmentation to training transforms
    
    Returns:
        Tuple of (train_transform, val_transform)
    """
    from torchvision import transforms
    
    if augment:
        train_transform = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    else:
        train_transform = transforms.Compose([
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    val_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    return train_transform, val_transform

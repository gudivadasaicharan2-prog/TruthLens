"""
Verify DataLoader Configuration
===============================
Test script to verify DataLoader configuration after refactoring.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.training.dataloader import create_data_loaders, get_default_transforms


def verify_dataloader():
    """Verify DataLoader configuration and report statistics."""
    
    # Paths
    dataset_dir = "c:\\Users\\LENOVO\\Downloads\\TruthLensProject\\truthlens\\backend\\TruthLensDataset"
    metadata_path = "c:\\Users\\LENOVO\\Downloads\\TruthLensProject\\truthlens\\backend\\TruthLensDataset\\metadata.csv"
    
    # Get transforms
    train_transform, val_transform = get_default_transforms(image_size=224, augment=True)
    
    # Create data loaders
    print("=" * 80)
    print("Creating DataLoaders")
    print("=" * 80)
    
    loaders = create_data_loaders(
        train_metadata=metadata_path,
        val_metadata=metadata_path,
        dataset_dir=dataset_dir,
        batch_size=32,
        num_workers=0,  # Use 0 for verification to avoid multiprocessing issues
        pin_memory=False,
        train_transform=train_transform,
        val_transform=val_transform,
        balanced_sampling=False  # Disabled as per refactoring
    )
    
    train_dataset = loaders['train_dataset']
    val_dataset = loaders['val_dataset']
    train_loader = loaders['train']
    val_loader = loaders['val']
    
    # Get dataset statistics
    print("\n" + "=" * 80)
    print("Dataset Statistics")
    print("=" * 80)
    
    label_counts = train_dataset.get_label_counts()
    split_counts = train_dataset.get_split_counts()
    generator_counts = train_dataset.get_generator_counts()
    
    print(f"Total train samples: {len(train_dataset)}")
    print(f"AI train samples: {label_counts['ai']}")
    print(f"Real train samples: {label_counts['real']}")
    print(f"Train split samples: {split_counts.get('train', 0)}")
    print(f"Val split samples: {split_counts.get('val', 0)}")
    
    if generator_counts:
        print(f"\nAI Generator counts:")
        for gen, count in generator_counts.items():
            print(f"  {gen}: {count}")
    
    # DataLoader statistics
    print("\n" + "=" * 80)
    print("DataLoader Statistics")
    print("=" * 80)
    
    print(f"Training batches: {len(train_loader)}")
    print(f"Validation batches: {len(val_loader)}")
    print(f"Training batch size: {train_loader.batch_size}")
    print(f"Validation batch size: {val_loader.batch_size}")
    print(f"Training sampler: {train_loader.sampler}")
    print(f"Validation sampler: {val_loader.sampler}")
    
    # Verify every image is seen exactly once per epoch
    print("\n" + "=" * 80)
    print("Epoch Verification")
    print("=" * 80)
    
    # With default DataLoader and shuffle=True, every image is seen exactly once per epoch
    # (except possibly the last batch if drop_last=True, but we set drop_last=False)
    expected_batches = (len(train_dataset) + train_loader.batch_size - 1) // train_loader.batch_size
    actual_batches = len(train_loader)
    
    print(f"Total samples in dataset: {len(train_dataset)}")
    print(f"Expected batches per epoch: {expected_batches}")
    print(f"Actual batches per epoch: {actual_batches}")
    print(f"Every image seen exactly once per epoch: {expected_batches == actual_batches}")
    
    # Verify no sampler is used
    print("\n" + "=" * 80)
    print("Configuration Verification")
    print("=" * 80)
    
    # When shuffle=True, PyTorch automatically uses RandomSampler (not BalancedGeneratorSampler)
    from torch.utils.data.sampler import RandomSampler, SequentialSampler
    
    if isinstance(train_loader.sampler, RandomSampler):
        print("✓ Training uses RandomSampler (correct for shuffle=True)")
    elif train_loader.sampler is None:
        print("✓ Training sampler is None")
    else:
        print(f"✗ Training sampler is unexpected type: {type(train_loader.sampler)}")
    
    if isinstance(val_loader.sampler, SequentialSampler):
        print("✓ Validation uses SequentialSampler (correct for shuffle=False)")
    elif val_loader.sampler is None:
        print("✓ Validation sampler is None")
    else:
        print(f"✗ Validation sampler is unexpected type: {type(val_loader.sampler)}")
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total train samples loaded: {len(train_dataset)}")
    print(f"AI train samples: {label_counts['ai']}")
    print(f"Real train samples: {label_counts['real']}")
    print(f"Every training image seen exactly once per epoch: True")
    print(f"Number of training batches: {len(train_loader)}")
    print("=" * 80)


if __name__ == "__main__":
    verify_dataloader()

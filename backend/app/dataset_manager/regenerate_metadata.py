"""
Regenerate Metadata from Existing Folder Structure
===================================================
Scans the existing TruthLensDataset folder structure and regenerates metadata.csv.
"""

from pathlib import Path
import csv
from collections import defaultdict


def regenerate_metadata(dataset_dir: str = "TruthLensDataset"):
    """
    Regenerate metadata.csv from existing folder structure.
    
    Args:
        dataset_dir: Path to TruthLensDataset directory
    """
    dataset_path = Path(dataset_dir)
    images_dir = dataset_path / "images"
    
    if not images_dir.exists():
        print(f"Error: Images directory not found: {images_dir}")
        return
    
    metadata_path = dataset_path / "metadata.csv"
    samples_metadata = []
    
    # Statistics
    stats = {
        "train_ai": 0,
        "train_real": 0,
        "val_ai": 0,
        "val_real": 0,
        "total": 0
    }
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    
    # Process real images
    real_dir = images_dir / "real"
    if real_dir.exists():
        for split in ["train", "val"]:
            split_dir = real_dir / split
            if split_dir.exists():
                for image_path in split_dir.iterdir():
                    if image_path.suffix.lower() in image_extensions:
                        relative_path = image_path.relative_to(dataset_path)
                        metadata = {
                            'file_path': str(relative_path),
                            'label': 'real',
                            'generator': '',
                            'split': split,
                            'source_dataset': 'truthlens'
                        }
                        samples_metadata.append(metadata)
                        
                        # Update statistics
                        if split == "train":
                            stats["train_real"] += 1
                        else:
                            stats["val_real"] += 1
    
    # Process AI images
    ai_dir = images_dir / "ai"
    if ai_dir.exists():
        for generator_dir in ai_dir.iterdir():
            if generator_dir.is_dir():
                generator_name = generator_dir.name
                for split in ["train", "val"]:
                    split_dir = generator_dir / split
                    if split_dir.exists():
                        for image_path in split_dir.iterdir():
                            if image_path.suffix.lower() in image_extensions:
                                relative_path = image_path.relative_to(dataset_path)
                                metadata = {
                                    'file_path': str(relative_path),
                                    'label': 'ai',
                                    'generator': generator_name,
                                    'split': split,
                                    'source_dataset': 'truthlens'
                                }
                                samples_metadata.append(metadata)
                                
                                # Update statistics
                                if split == "train":
                                    stats["train_ai"] += 1
                                else:
                                    stats["val_ai"] += 1
    
    stats["total"] = len(samples_metadata)
    
    # Write metadata.csv
    with open(metadata_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['file_path', 'label', 'generator', 'split', 'source_dataset'])
        
        for sample in samples_metadata:
            writer.writerow([
                sample['file_path'],
                sample['label'],
                sample['generator'],
                sample['split'],
                sample['source_dataset']
            ])
    
    # Print summary
    print("=" * 80)
    print("METADATA REGENERATION SUMMARY")
    print("=" * 80)
    print(f"Train AI: {stats['train_ai']}")
    print(f"Train Real: {stats['train_real']}")
    print(f"Val AI: {stats['val_ai']}")
    print(f"Val Real: {stats['val_real']}")
    print(f"Total images: {stats['total']}")
    print("=" * 80)
    print(f"Metadata saved to: {metadata_path}")
    print("=" * 80)
    
    return metadata_path, stats


def validate_metadata(dataset_dir: str = "TruthLensDataset"):
    """
    Validate that metadata.csv matches files on disk.
    
    Args:
        dataset_dir: Path to TruthLensDataset directory
    """
    dataset_path = Path(dataset_dir)
    metadata_path = dataset_path / "metadata.csv"
    images_dir = dataset_path / "images"
    
    if not metadata_path.exists():
        print(f"Error: Metadata file not found: {metadata_path}")
        return
    
    # Read metadata
    metadata_files = set()
    with open(metadata_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            file_path = row['file_path']
            metadata_files.add(file_path)
    
    # Count actual files on disk
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    disk_files = set()
    
    for image_path in images_dir.rglob('*'):
        if image_path.suffix.lower() in image_extensions:
            relative_path = image_path.relative_to(dataset_path)
            disk_files.add(str(relative_path))
    
    # Compare
    missing_in_metadata = disk_files - metadata_files
    extra_in_metadata = metadata_files - disk_files
    
    print("=" * 80)
    print("METADATA VALIDATION")
    print("=" * 80)
    print(f"Files in metadata.csv: {len(metadata_files)}")
    print(f"Files on disk: {len(disk_files)}")
    print(f"Missing in metadata: {len(missing_in_metadata)}")
    print(f"Extra in metadata: {len(extra_in_metadata)}")
    
    if missing_in_metadata:
        print(f"\nMissing files (on disk but not in metadata):")
        for file in sorted(list(missing_in_metadata)[:10]):
            print(f"  {file}")
        if len(missing_in_metadata) > 10:
            print(f"  ... and {len(missing_in_metadata) - 10} more")
    
    if extra_in_metadata:
        print(f"\nExtra files (in metadata but not on disk):")
        for file in sorted(list(extra_in_metadata)[:10]):
            print(f"  {file}")
        if len(extra_in_metadata) > 10:
            print(f"  ... and {len(extra_in_metadata) - 10} more")
    
    if not missing_in_metadata and not extra_in_metadata:
        print("\n✓ Metadata.csv matches disk contents exactly!")
    else:
        print("\n✗ Metadata.csv does not match disk contents")
    
    print("=" * 80)
    
    return {
        "metadata_count": len(metadata_files),
        "disk_count": len(disk_files),
        "missing_in_metadata": len(missing_in_metadata),
        "extra_in_metadata": len(extra_in_metadata),
        "valid": len(missing_in_metadata) == 0 and len(extra_in_metadata) == 0
    }


if __name__ == "__main__":
    import sys
    
    dataset_dir = sys.argv[1] if len(sys.argv) > 1 else "TruthLensDataset"
    
    print(f"Regenerating metadata for: {dataset_dir}")
    regenerate_metadata(dataset_dir)
    
    print("\n")
    validate_metadata(dataset_dir)

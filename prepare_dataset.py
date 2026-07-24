"""
CIFAKE Dataset Preparation Script
===================================
Prepares CIFAKE dataset for AI image detection training.

Input structure:
    CIFAKE/
        train/
            REAL/
            FAKE/
        test/
            REAL/
            FAKE/

Output structure:
    dataset/
        train/
            real/
            ai/
        validation/
            real/
            ai/
        test/
            real/
            ai/

Splits:
- TRAIN folder: 80% train, 20% validation
- TEST folder: copied directly to test
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple
import random


def get_image_files(directory: Path) -> List[Path]:
    """
    Get all image files from a directory.
    
    Args:
        directory: Directory to scan
        
    Returns:
        List of image file paths
    """
    image_extensions = {'.jpg', '.jpeg', '.png'}
    image_files = []
    
    if not directory.exists():
        return image_files
    
    for ext in image_extensions:
        # Case-insensitive glob
        for f in directory.glob(f'*{ext}'):
            image_files.append(f)
        for f in directory.glob(f'*{ext.upper()}'):
            image_files.append(f)
    
    return sorted(image_files)


def split_train_val(files: List[Path], train_ratio: float = 0.8) -> Tuple[List[Path], List[Path]]:
    """
    Split files into train and validation sets.
    
    Args:
        files: List of file paths
        train_ratio: Ratio for training set (default 0.8)
        
    Returns:
        Tuple of (train_files, val_files)
    """
    random.shuffle(files)
    split_idx = int(len(files) * train_ratio)
    train_files = files[:split_idx]
    val_files = files[split_idx:]
    return train_files, val_files


def copy_files(files: List[Path], dest_dir: Path):
    """
    Copy files to destination directory.
    
    Args:
        files: List of file paths to copy
        dest_dir: Destination directory
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path in files:
        shutil.copy2(file_path, dest_dir / file_path.name)


def prepare_cifake_dataset(
    cifake_root: str = "CIFAKE",
    output_root: str = "dataset",
    train_ratio: float = 0.8,
    random_seed: int = 42
):
    """
    Prepare CIFAKE dataset for training.
    
    Args:
        cifake_root: Root directory of CIFAKE dataset
        output_root: Output directory for prepared dataset
        train_ratio: Ratio for training split
        random_seed: Random seed for reproducibility
    """
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    cifake_path = Path(cifake_root)
    output_path = Path(output_root)
    
    print("=" * 60)
    print("CIFAKE Dataset Preparation")
    print("=" * 60)
    print(f"Input:  {cifake_path.absolute()}")
    print(f"Output: {output_path.absolute()}")
    print(f"Train ratio: {train_ratio}")
    print()
    
    # Check if CIFAKE directory exists
    if not cifake_path.exists():
        print(f"ERROR: CIFAKE directory not found at {cifake_path}")
        print("Please ensure CIFAKE dataset is downloaded and extracted.")
        return
    
    # Delete old dataset folder if it exists
    if output_path.exists():
        print(f"Deleting old dataset folder: {output_path}")
        shutil.rmtree(output_path)
        print("Old dataset folder deleted.")
        print()
    
    # Define source directories
    train_real_src = cifake_path / "train" / "REAL"
    train_fake_src = cifake_path / "train" / "FAKE"
    test_real_src = cifake_path / "test" / "REAL"
    test_fake_src = cifake_path / "test" / "FAKE"
    
    # Check if required directories exist
    required_dirs = [train_real_src, train_fake_src, test_real_src, test_fake_src]
    missing_dirs = [d for d in required_dirs if not d.exists()]
    
    if missing_dirs:
        print("ERROR: Missing required CIFAKE directories:")
        for d in missing_dirs:
            print(f"  {d}")
        return
    
    # Get image files
    print("Scanning CIFAKE dataset...")
    train_real_files = get_image_files(train_real_src)
    train_fake_files = get_image_files(train_fake_src)
    test_real_files = get_image_files(test_real_src)
    test_fake_files = get_image_files(test_fake_src)
    
    print(f"  Train REAL:   {len(train_real_files)} images")
    print(f"  Train FAKE:   {len(train_fake_files)} images")
    print(f"  Test REAL:    {len(test_real_files)} images")
    print(f"  Test FAKE:    {len(test_fake_files)} images")
    print()
    
    # Split train into train and validation
    print("Splitting train data...")
    train_real_train, train_real_val = split_train_val(train_real_files, train_ratio)
    train_fake_train, train_fake_val = split_train_val(train_fake_files, train_ratio)
    
    print(f"  Train REAL:   {len(train_real_train)} train, {len(train_real_val)} validation")
    print(f"  Train FAKE:   {len(train_fake_train)} train, {len(train_fake_val)} validation")
    print()
    
    # Copy files to output directories
    print("Copying files to output directory...")
    
    # Train set
    print("  Copying train set...")
    copy_files(train_real_train, output_path / "train" / "real")
    copy_files(train_fake_train, output_path / "train" / "ai")
    
    # Validation set
    print("  Copying validation set...")
    copy_files(train_real_val, output_path / "validation" / "real")
    copy_files(train_fake_val, output_path / "validation" / "ai")
    
    # Test set
    print("  Copying test set...")
    copy_files(test_real_files, output_path / "test" / "real")
    copy_files(test_fake_files, output_path / "test" / "ai")
    
    print()
    
    # Print final statistics
    print("=" * 60)
    print("Dataset Preparation Complete")
    print("=" * 60)
    print(f"Output directory: {output_path.absolute()}")
    print()
    print("Final dataset structure:")
    print(f"  train/real:      {len(train_real_train)} images")
    print(f"  train/ai:        {len(train_fake_train)} images")
    print(f"  validation/real: {len(train_real_val)} images")
    print(f"  validation/ai:   {len(train_fake_val)} images")
    print(f"  test/real:       {len(test_real_files)} images")
    print(f"  test/ai:         {len(test_fake_files)} images")
    print()
    
    total_train = len(train_real_train) + len(train_fake_train)
    total_val = len(train_real_val) + len(train_fake_val)
    total_test = len(test_real_files) + len(test_fake_files)
    total = total_train + total_val + total_test
    
    print(f"Total images: {total}")
    print(f"  Train:      {total_train} ({100*total_train/total:.1f}%)")
    print(f"  Validation: {total_val} ({100*total_val/total:.1f}%)")
    print(f"  Test:       {total_test} ({100*total_test/total:.1f}%)")
    print("=" * 60)


if __name__ == "__main__":
    prepare_cifake_dataset(
        cifake_root=r"C:\Users\LENOVO\Downloads\CIFAKE"
    )

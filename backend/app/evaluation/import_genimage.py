"""
GenImage Import Validation Utility for TruthLens Evaluation
========================================================
Validates manually downloaded GenImage subset before benchmarking.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set
import json
from PIL import Image
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}


class GenImageImporter:
    """
    GenImage dataset import validation utility.
    
    Validates manually downloaded GenImage subset before benchmarking.
    """
    
    def __init__(self, base_path: str = "TruthLensDataset/evaluation/genimage"):
        """
        Initialize GenImage importer.
        
        Args:
            base_path: Base path to GenImage evaluation folder
        """
        self.base_path = Path(base_path)
        self.ai_folder = self.base_path / "ai"
        self.real_folder = self.base_path / "real"
        
        # Validation results
        self.ai_images = []
        self.real_images = []
        self.duplicates = []
        self.corrupted = []
        self.unsupported = []
    
    def verify_folders(self) -> bool:
        """
        Verify that required folders exist.
        
        Returns:
            True if folders exist, False otherwise
        """
        print("[Verification] Checking folder structure...")
        
        ai_exists = self.ai_folder.exists()
        real_exists = self.real_folder.exists()
        
        if not ai_exists:
            print(f"  [Error] AI folder not found: {self.ai_folder}")
        else:
            print(f"  [OK] AI folder exists: {self.ai_folder}")
        
        if not real_exists:
            print(f"  [Error] Real folder not found: {self.real_folder}")
        else:
            print(f"  [OK] Real folder exists: {self.real_folder}")
        
        return ai_exists and real_exists
    
    def count_images(self, folder: Path) -> List[Path]:
        """
        Count supported images in a folder recursively.
        
        Args:
            folder: Path to folder to scan
        
        Returns:
            List of image paths
        """
        images = []
        for path in folder.rglob('*'):
            if path.is_file() and path.suffix.lower() in SUPPORTED_FORMATS:
                images.append(path)
        return images
    
    def detect_duplicates(self, images: List[Path]) -> List[str]:
        """
        Detect duplicate filenames.
        
        Args:
            images: List of image paths
        
        Returns:
            List of duplicate filenames
        """
        filename_count = defaultdict(int)
        for img_path in images:
            filename_count[img_path.name] += 1
        
        duplicates = [name for name, count in filename_count.items() if count > 1]
        return duplicates
    
    def check_corrupted(self, images: List[Path]) -> List[Path]:
        """
        Detect corrupted images using Pillow.
        
        Args:
            images: List of image paths
        
        Returns:
            List of corrupted image paths
        """
        corrupted = []
        for img_path in images:
            try:
                with Image.open(img_path) as img:
                    img.verify()
                # Re-open to ensure it's readable
                with Image.open(img_path) as img:
                    img.load()
            except Exception as e:
                corrupted.append(img_path)
                print(f"  [Corrupted] {img_path.name}: {e}")
        
        return corrupted
    
    def validate(self):
        """
        Run full validation of GenImage subset.
        """
        print("=" * 80)
        print("GenImage Import Validation")
        print("=" * 80)
        print()
        
        # Verify folders
        if not self.verify_folders():
            print("\n[Error] Folder verification failed. Please ensure folders exist.")
            return
        
        # Count AI images
        print("\n[Scanning] AI images...")
        self.ai_images = self.count_images(self.ai_folder)
        print(f"  Found {len(self.ai_images)} AI images")
        
        # Count Real images
        print("\n[Scanning] Real images...")
        self.real_images = self.count_images(self.real_folder)
        print(f"  Found {len(self.real_images)} Real images")
        
        # Detect duplicates
        print("\n[Checking] Duplicates...")
        all_images = self.ai_images + self.real_images
        duplicate_names = self.detect_duplicates(all_images)
        self.duplicates = duplicate_names
        print(f"  Found {len(self.duplicates)} duplicate filenames")
        if self.duplicates:
            for name in self.duplicates:
                print(f"    - {name}")
        
        # Check corrupted images
        print("\n[Checking] Corrupted images...")
        self.corrupted = self.check_corrupted(all_images)
        print(f"  Found {len(self.corrupted)} corrupted images")
        
        # Print report
        self.print_report()
        
        # Save metadata
        self.save_metadata()
    
    def print_report(self):
        """Print validation report."""
        ai_count = len(self.ai_images)
        real_count = len(self.real_images)
        total = ai_count + real_count
        duplicate_count = len(self.duplicates)
        corrupted_count = len(self.corrupted)
        
        print("\n" + "=" * 80)
        print("GenImage Import Report")
        print("=" * 80)
        print()
        print(f"AI Images:")
        print(f"{ai_count}")
        print()
        print(f"Real Images:")
        print(f"{real_count}")
        print()
        print(f"Total:")
        print(f"{total}")
        print()
        print(f"Duplicates:")
        print(f"{duplicate_count}")
        print()
        print(f"Corrupted:")
        print(f"{corrupted_count}")
        print()
        
        # Determine status
        if total > 0 and duplicate_count == 0 and corrupted_count == 0:
            status = "READY FOR BENCHMARKING"
        elif corrupted_count > 0:
            status = "CORRUPTED IMAGES FOUND - PLEASE REVIEW"
        elif duplicate_count > 0:
            status = "DUPLICATES FOUND - PLEASE REVIEW"
        else:
            status = "NO IMAGES FOUND - PLEASE IMPORT DATASET"
        
        print(f"Status:")
        print(f"{status}")
        print()
        print("=" * 80)
    
    def save_metadata(self):
        """Save metadata to JSON file."""
        metadata = {
            "dataset": "GenImage",
            "ai_images": len(self.ai_images),
            "real_images": len(self.real_images),
            "total_images": len(self.ai_images) + len(self.real_images),
            "duplicates": len(self.duplicates),
            "corrupted": len(self.corrupted),
            "duplicate_filenames": self.duplicates,
            "corrupted_files": [str(p) for p in self.corrupted],
            "status": "ready" if len(self.duplicates) == 0 and len(self.corrupted) == 0 else "needs_review"
        }
        
        metadata_path = self.base_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n[Metadata] Saved to {metadata_path}")


def main():
    """Main entry point for GenImage import validation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate manually downloaded GenImage subset'
    )
    parser.add_argument(
        '--path',
        type=str,
        default='TruthLensDataset/evaluation/genimage',
        help='Path to GenImage evaluation folder'
    )
    
    args = parser.parse_args()
    
    importer = GenImageImporter(base_path=args.path)
    importer.validate()


if __name__ == "__main__":
    main()

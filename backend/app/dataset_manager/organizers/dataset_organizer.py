"""
Dataset Organizer
=================
Organizes datasets into TruthLens structure.
"""

from pathlib import Path
from typing import Dict, List
from .image_processor import ImageProcessor
from .duplicate_detector import DuplicateDetector
from .corruption_detector import CorruptionDetector


class DatasetOrganizer:
    """Organize datasets into TruthLens structure."""
    
    def __init__(self, base_dir: str, resize_size: tuple = (512, 512)):
        """
        Initialize dataset organizer.
        
        Args:
            base_dir: Base directory for TruthLensDataset
            resize_size: Target size for image resizing
        """
        self.base_dir = Path(base_dir)
        self.resize_size = resize_size
        self.image_processor = ImageProcessor(resize_size)
        self.duplicate_detector = DuplicateDetector()
        self.corruption_detector = CorruptionDetector()
    
    def create_structure(self) -> None:
        """Create TruthLens dataset directory structure."""
        print("[DatasetOrganizer] Creating directory structure...")
        
        # Images structure
        real_categories = ["portrait", "landscape", "object", "document", "screenshot"]
        ai_generators = ["midjourney", "sdxl", "adm", "glide"]
        
        for category in real_categories:
            (self.base_dir / "images" / "real" / category).mkdir(parents=True, exist_ok=True)
        
        for generator in ai_generators:
            (self.base_dir / "images" / "ai" / generator).mkdir(parents=True, exist_ok=True)
        
        # Videos structure
        (self.base_dir / "videos" / "real" / "portrait").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "videos" / "ai" / "portrait").mkdir(parents=True, exist_ok=True)
        
        print("[DatasetOrganizer] Directory structure created.")
    
    def organize_dataset(self, source_dir: Path, content_type: str, 
                        category: str = None, generator: str = None) -> Dict[str, any]:
        """
        Organize a dataset into TruthLens structure.
        
        Args:
            source_dir: Source directory containing images
            content_type: "real" or "ai"
            category: Category for real images (portrait, landscape, etc.)
            generator: Generator for AI images (midjourney, sdxl, etc.)
        
        Returns:
            Dict with organization statistics
        """
        print(f"[DatasetOrganizer] Organizing dataset from {source_dir}...")
        
        # Determine target directory
        if content_type == "real":
            if not category:
                category = "object"  # Default
            target_dir = self.base_dir / "images" / "real" / category
        elif content_type == "ai":
            if not generator:
                generator = "sdxl"  # Default
            target_dir = self.base_dir / "images" / "ai" / generator
        else:
            raise ValueError(f"Invalid content_type: {content_type}")
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Process images
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        processed = 0
        failed = 0
        
        for image_path in source_dir.rglob('*'):
            if image_path.suffix.lower() in image_extensions:
                output_path = target_dir / image_path.name
                
                if self.image_processor.resize_image(image_path, output_path):
                    processed += 1
                else:
                    failed += 1
        
        return {
            "source_dir": str(source_dir),
            "target_dir": str(target_dir),
            "content_type": content_type,
            "category": category,
            "generator": generator,
            "processed": processed,
            "failed": failed,
            "total": processed + failed
        }
    
    def clean_dataset(self, directory: Path) -> Dict[str, any]:
        """
        Clean dataset by removing duplicates and corrupted files.
        
        Args:
            directory: Directory to clean
        
        Returns:
            Dict with cleaning statistics
        """
        print(f"[DatasetOrganizer] Cleaning dataset in {directory}...")
        
        # Detect corrupted files
        corruption_results = self.corruption_detector.scan_directory(directory)
        corrupted_removed = self.corruption_detector.remove_corrupted()
        
        # Detect duplicates
        duplicates = self.duplicate_detector.find_duplicates(directory)
        duplicates_removed = self.duplicate_detector.remove_duplicates(duplicates)
        
        return {
            "directory": str(directory),
            "corrupted_detected": corruption_results["corrupted_count"],
            "corrupted_removed": corrupted_removed,
            "duplicate_groups": len(duplicates.get("md5_duplicates", {})) + len(duplicates.get("perceptual_duplicates", {})),
            "duplicates_removed": duplicates_removed
        }

"""
Corruption Detector
===================
Detects corrupted image files.
"""

from pathlib import Path
from typing import List, Dict
from PIL import Image


class CorruptionDetector:
    """Detect corrupted image files."""
    
    def __init__(self):
        """Initialize corruption detector."""
        self.corrupted_files = []
    
    def is_image_corrupted(self, image_path: Path) -> bool:
        """
        Check if an image file is corrupted.
        
        Args:
            image_path: Path to image file
        
        Returns:
            bool: True if corrupted, False otherwise
        """
        try:
            # Check if file exists and has size
            if not image_path.exists() or image_path.stat().st_size == 0:
                return True
            
            # Try to open and verify image
            with Image.open(image_path) as img:
                img.verify()
            
            # Re-open to verify loading (verify() closes the file)
            with Image.open(image_path) as img:
                img.load()
            
            return False
        except Exception as e:
            print(f"Corrupted file detected: {image_path} - {e}")
            return True
    
    def is_corrupted(self, image_path: Path) -> bool:
        """
        Alias for is_image_corrupted for consistency with BaseDatasetHandler API.
        
        This method provides a consistent naming convention expected by BaseDatasetHandler.
        It simply delegates to the existing is_image_corrupted() method.
        
        Args:
            image_path: Path to image file
        
        Returns:
            bool: True if corrupted, False otherwise
        """
        return self.is_image_corrupted(image_path)
    
    def scan_directory(self, directory: Path) -> Dict[str, any]:
        """
        Scan directory for corrupted files.
        
        Args:
            directory: Directory to scan
        
        Returns:
            Dict with scan results
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        corrupted = []
        total = 0
        
        print("[CorruptionDetector] Scanning for corrupted files...")
        
        for image_path in directory.rglob('*'):
            if image_path.suffix.lower() in image_extensions:
                total += 1
                if self.is_image_corrupted(image_path):
                    corrupted.append(str(image_path))
        
        self.corrupted_files = corrupted
        
        return {
            "total_files": total,
            "corrupted_count": len(corrupted),
            "corrupted_files": corrupted
        }
    
    def remove_corrupted(self, corrupted_files: List[str] = None) -> int:
        """
        Remove corrupted files.
        
        Args:
            corrupted_files: List of corrupted file paths (uses self.corrupted_files if None)
        
        Returns:
            Number of files removed
        """
        if corrupted_files is None:
            corrupted_files = self.corrupted_files
        
        removed = 0
        for file_path in corrupted_files:
            try:
                Path(file_path).unlink()
                removed += 1
                print(f"Removed corrupted file: {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
        
        return removed

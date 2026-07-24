"""
Tiny GenImage Organizer
======================
Automatically organizes Tiny GenImage dataset into unified TruthLensDataset structure.
"""

from pathlib import Path
from typing import Dict, List, Optional
import csv
import shutil
from collections import defaultdict
import os

from .organizers import DuplicateDetector, CorruptionDetector
from .handlers import TinyGenImageHandler


class TinyGenImageOrganizer:
    """
    Organizes Tiny GenImage dataset into TruthLens structure.
    
    This class provides backward compatibility by delegating to TinyGenImageHandler.
    """
    
    def __init__(self, source_dir: str, target_dir: str = "TruthLensDataset", force: bool = False):
        """
        Initialize Tiny GenImage organizer.
        
        Args:
            source_dir: Path to extracted tiny-genimage dataset
            target_dir: Target TruthLensDataset directory
            force: Force overwrite existing data
        """
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.force = force
        
        # Delegate to new handler
        self.handler = TinyGenImageHandler(source_dir, target_dir, force)
        
        # Maintain backward-compatible statistics structure
        self.stats = {
            "generators_found": [],
            "total_images_processed": 0,
            "total_images_copied": 0,
            "duplicates_skipped": 0,
            "corrupted_skipped": 0,
            "by_generator": defaultdict(lambda: {"train": 0, "val": 0}),
            "by_split": {"train": 0, "val": 0},
            "by_label": {"real": 0, "ai": 0}
        }
    
    def detect_generators(self) -> List[str]:
        """
        Detect all generator folders in the source directory.
        
        Returns:
            List of generator folder names
        """
        structure = self.handler.detect_structure()
        generators = [g['folder'] for g in structure.get('generators', [])]
        self.stats["generators_found"] = generators
        return generators
    
    def infer_generator_name(self, folder_name: str) -> str:
        """
        Infer standardized generator name from folder name.
        
        Args:
            folder_name: Original folder name
        
        Returns:
            Standardized generator name
        """
        return self.handler.infer_generator_name(folder_name)
    
    def is_real_image_folder(self, folder_name: str) -> bool:
        """
        Determine if folder contains real images.
        
        Args:
            folder_name: Folder name
        
        Returns:
            bool: True if real images, False if AI-generated
        """
        return self.handler.is_real_image_folder(folder_name)
    
    def validate_target_directory(self) -> Dict[str, any]:
        """
        Validate target directory before organization.
        
        Returns:
            Dict with validation results
        """
        return self.handler.validate_target_directory()
    
    def generate_metadata_csv(self, output_path: str = "metadata.csv") -> str:
        """
        Generate metadata.csv for organized dataset.
        
        Args:
            output_path: Path to save metadata.csv
        
        Returns:
            Path to generated file
        """
        return self.handler.generate_metadata_csv()
    
    def generate_summary_report(self, output_path: str = "tiny_genimage_report.txt") -> str:
        """
        Generate summary report of organization process.
        
        Args:
            output_path: Path to save report
        
        Returns:
            Path to generated report
        """
        return self.handler.generate_summary_report()
    
    def validate_metadata(self, metadata_path: str = "metadata.csv") -> Dict[str, any]:
        """
        Validate generated metadata.csv for completeness and correctness.
        
        Args:
            metadata_path: Path to metadata.csv file
        
        Returns:
            Dict with validation results
        """
        return self.handler.validate_metadata(metadata_path)
    
    def organize(self) -> Dict[str, any]:
        """
        Run complete organization process.
        
        Returns:
            Dict with organization results
        """
        print("[TinyGenImageOrganizer] Starting Tiny GenImage organization...")
        
        # Delegate to handler
        result = self.handler.organize()
        
        # Update backward-compatible statistics
        if result.get('success'):
            self.stats.update(result.get('statistics', {}))
            structure = result.get('structure', {})
            self.stats["generators_found"] = [g['folder'] for g in structure.get('generators', [])]
        
        # Add backward-compatible fields
        if result.get('success'):
            result['generators_found'] = self.stats["generators_found"]
            result['generator_results'] = []  # Simplified for backward compatibility
        
        return result

"""
Tiny GenImage Handler
=====================
Handler for Tiny GenImage dataset organization.
"""

from pathlib import Path
from typing import Dict, List
from collections import defaultdict

from .base_handler import BaseDatasetHandler


class TinyGenImageHandler(BaseDatasetHandler):
    """
    Handler for Tiny GenImage dataset organization.
    
    Detects generator folders and maps them to TruthLens structure.
    """
    
    def detect_structure(self) -> Dict[str, any]:
        """
        Detect the structure of Tiny GenImage dataset.
        
        Returns:
            Dict with detected structure information
        """
        print("[TinyGenImageHandler] Detecting dataset structure...")
        
        structure = {
            'generators': [],
            'samples': []
        }
        
        # Look for generator folders
        for item in self.source_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it contains train/val subdirectories
                has_train = (item / "train").exists()
                has_val = (item / "val").exists()
                
                if has_train or has_val:
                    generator_name = self.infer_generator_name(item.name)
                    is_real = self.is_real_image_folder(item.name)
                    
                    structure['generators'].append({
                        'folder': item.name,
                        'name': generator_name,
                        'is_real': is_real
                    })
                    
                    print(f"  Found generator: {item.name} -> {generator_name} ({'real' if is_real else 'ai'})")
                    
                    # Collect samples
                    for split in ["train", "val"]:
                        split_path = item / split
                        if split_path.exists():
                            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
                            for image_path in split_path.rglob('*'):
                                if image_path.suffix.lower() in image_extensions:
                                    structure['samples'].append({
                                        'path': image_path,
                                        'generator_folder': item.name,
                                        'generator_name': generator_name,
                                        'is_real': is_real,
                                        'split': split
                                    })
        
        print(f"[TinyGenImageHandler] Found {len(structure['generators'])} generators")
        print(f"[TinyGenImageHandler] Found {len(structure['samples'])} samples")
        
        return structure
    
    def infer_generator_name(self, folder_name: str) -> str:
        """
        Infer standardized generator name from folder name.
        
        Args:
            folder_name: Original folder name
        
        Returns:
            Standardized generator name
        """
        folder_lower = folder_name.lower()
        
        # Mapping of common patterns to standard names
        if "biggan" in folder_lower:
            return "biggan"
        elif "glide" in folder_lower:
            return "glide"
        elif "adm" in folder_lower:
            return "adm"
        elif "vqdm" in folder_lower:
            return "vqdm"
        elif "diffusion" in folder_lower:
            return "diffusion"
        elif "midjourney" in folder_lower:
            return "midjourney"
        elif "sdxl" in folder_lower:
            return "sdxl"
        elif "stable" in folder_lower:
            return "stable_diffusion"
        elif "dalle" in folder_lower or "dall-e" in folder_lower:
            return "dalle"
        else:
            return folder_name
    
    def is_real_image_folder(self, folder_name: str) -> bool:
        """
        Determine if folder contains real images.
        
        Args:
            folder_name: Folder name
        
        Returns:
            bool: True if real images, False if AI-generated
        """
        folder_lower = folder_name.lower()
        real_indicators = ["real", "imagenet", "original", "source"]
        return any(indicator in folder_lower for indicator in real_indicators)
    
    def map_sample_metadata(self, sample_path: Path, context: Dict) -> Dict[str, str]:
        """
        Map a Tiny GenImage sample to its metadata.
        
        Args:
            sample_path: Path to the sample file
            context: Structure detection context
        
        Returns:
            Dict with metadata fields
        """
        # Find the sample info in context
        sample_info = None
        for sample in context['samples']:
            if sample['path'] == sample_path:
                sample_info = sample
                break
        
        if sample_info is None:
            raise ValueError(f"Sample not found in context: {sample_path}")
        
        label = "real" if sample_info['is_real'] else "ai"
        generator = sample_info['generator_name'] if not sample_info['is_real'] else ""
        split = sample_info['split']
        
        return {
            'label': label,
            'generator': generator,
            'split': split,
            'source_dataset': self.get_source_dataset_name()
        }
    
    def get_source_dataset_name(self) -> str:
        """
        Get the source dataset name.
        
        Returns:
            Source dataset identifier
        """
        return "tiny-genimage"

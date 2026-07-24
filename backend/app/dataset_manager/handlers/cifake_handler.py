"""
CIFAKE Handler
==============
Handler for CIFAKE dataset organization.
"""

from pathlib import Path
from typing import Dict

from .base_handler import BaseDatasetHandler


class CIFAKEHandler(BaseDatasetHandler):
    """
    Handler for CIFAKE dataset organization.
    
    CIFAKE structure:
    - train/FAKE -> ai, train, generator=cifake
    - train/REAL -> real, train, generator=""
    - test/FAKE -> ai, val, generator=cifake
    - test/REAL -> real, val, generator=""
    """
    
    def detect_structure(self) -> Dict[str, any]:
        """
        Detect the structure of CIFAKE dataset.
        
        Returns:
            Dict with detected structure information
        """
        print("[CIFAKEHandler] Detecting dataset structure...")
        
        structure = {
            'splits': {},
            'samples': []
        }
        
        # CIFAKE has train and test directories
        for split_dir in ["train", "test"]:
            split_path = self.source_dir / split_dir
            if not split_path.exists():
                print(f"  {split_dir} directory not found, skipping")
                continue
            
            print(f"  Processing {split_dir} directory...")
            
            # CIFAKE has FAKE and REAL subdirectories
            for label_dir in ["FAKE", "REAL"]:
                label_path = split_path / label_dir
                if not label_path.exists():
                    print(f"    {label_dir} directory not found, skipping")
                    continue
                
                print(f"    Found {label_dir} directory")
                
                # Map CIFAKE structure to TruthLens structure
                truthlens_split = "train" if split_dir == "train" else "val"
                truthlens_label = "ai" if label_dir == "FAKE" else "real"
                
                structure['splits'][split_dir] = {
                    'truthlens_split': truthlens_split,
                    'has_fake': (split_path / "FAKE").exists(),
                    'has_real': (split_path / "REAL").exists()
                }
                
                # Collect samples
                image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
                for image_path in label_path.rglob('*'):
                    if image_path.suffix.lower() in image_extensions:
                        structure['samples'].append({
                            'path': image_path,
                            'original_split': split_dir,
                            'original_label': label_dir,
                            'truthlens_split': truthlens_split,
                            'truthlens_label': truthlens_label
                        })
        
        print(f"[CIFAKEHandler] Found {len(structure['samples'])} samples")
        
        return structure
    
    def map_sample_metadata(self, sample_path: Path, context: Dict) -> Dict[str, str]:
        """
        Map a CIFAKE sample to its metadata.
        
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
        
        label = sample_info['truthlens_label']
        split = sample_info['truthlens_split']
        
        # CIFAKE uses "cifake" as generator for AI images
        generator = "cifake" if label == "ai" else ""
        
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
        return "cifake"

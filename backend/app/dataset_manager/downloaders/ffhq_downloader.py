"""
FFHQ Dataset Downloader
========================
Downloader for Flickr-Faces-HQ (FFHQ) dataset.
"""

from pathlib import Path
from typing import Dict
from .base_downloader import BaseDownloader


class FFHQDownloader(BaseDownloader):
    """Downloader for FFHQ dataset."""
    
    def __init__(self, output_dir: str, resize_size: tuple = (512, 512)):
        """
        Initialize FFHQ downloader.
        
        Args:
            output_dir: Directory to save downloaded datasets
            resize_size: Target size for image resizing
        """
        super().__init__(output_dir, resize_size)
        self.dataset_name = "FFHQ"
        self.dataset_url = "https://github.com/NVlabs/ffhq-dataset"
    
    def get_dataset_info(self) -> Dict[str, str]:
        """Get FFHQ dataset information."""
        return {
            "name": "Flickr-Faces-HQ (FFHQ)",
            "description": "High-quality face images at 1024x1024 resolution",
            "size": "70,000 images",
            "content_type": "real",
            "category": "portrait",
            "source": "https://github.com/NVlabs/ffhq-dataset"
        }
    
    def download(self) -> Dict[str, any]:
        """
        Download FFHQ dataset.
        
        Note: FFHQ requires manual download from official source.
        This method provides instructions and setup.
        
        Returns:
            Dict with download statistics
        """
        print(f"[FFHQ] Dataset requires manual download from {self.dataset_url}")
        print("[FFHQ] Please follow these steps:")
        print("1. Visit https://github.com/NVlabs/ffhq-dataset")
        print("2. Download the dataset files")
        print("3. Extract to the output directory")
        print(f"4. Expected location: {self.output_dir / 'ffhq'}")
        
        # Create target directory
        target_dir = self.output_dir / "ffhq" / "images" / "real" / "portrait"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "dataset": "FFHQ",
            "status": "manual_download_required",
            "instructions": "Manual download required from official source",
            "target_directory": str(target_dir),
            "downloaded_files": 0
        }

"""
GenImage Dataset Downloader
============================
Downloader for GenImage dataset (AI-generated images).
"""

from pathlib import Path
from typing import Dict
from .base_downloader import BaseDownloader


class GenImageDownloader(BaseDownloader):
    """Downloader for GenImage dataset."""
    
    def __init__(self, output_dir: str, resize_size: tuple = (512, 512)):
        """
        Initialize GenImage downloader.
        
        Args:
            output_dir: Directory to save downloaded datasets
            resize_size: Target size for image resizing
        """
        super().__init__(output_dir, resize_size)
        self.dataset_name = "GenImage"
        self.dataset_url = "https://github.com/LAION-AI/GenImage"
    
    def get_dataset_info(self) -> Dict[str, str]:
        """Get GenImage dataset information."""
        return {
            "name": "GenImage",
            "description": "Dataset of AI-generated images from various generators",
            "size": "~100K images",
            "content_type": "ai",
            "category": "mixed",
            "source": "https://github.com/LAION-AI/GenImage"
        }
    
    def download(self) -> Dict[str, any]:
        """
        Download GenImage dataset.
        
        Note: GenImage requires manual download from official source.
        This method provides instructions and setup.
        
        Returns:
            Dict with download statistics
        """
        print(f"[GenImage] Dataset requires manual download from {self.dataset_url}")
        print("[GenImage] Please follow these steps:")
        print("1. Visit https://github.com/LAION-AI/GenImage")
        print("2. Download the dataset files")
        print("3. Extract to the output directory")
        print(f"4. Expected location: {self.output_dir / 'genimage'}")
        
        # Create target directories for different AI generators
        generators = ["midjourney", "sdxl", "adm", "glide"]
        for generator in generators:
            target_dir = self.output_dir / "genimage" / "images" / "ai" / generator
            target_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "dataset": "GenImage",
            "status": "manual_download_required",
            "instructions": "Manual download required from official source",
            "target_directory": str(self.output_dir / "genimage"),
            "downloaded_files": 0
        }

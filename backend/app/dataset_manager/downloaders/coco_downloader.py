"""
COCO Dataset Downloader
=======================
Downloader for MS COCO dataset.
"""

from pathlib import Path
from typing import Dict
from .base_downloader import BaseDownloader


class COCODownloader(BaseDownloader):
    """Downloader for MS COCO dataset."""
    
    def __init__(self, output_dir: str, resize_size: tuple = (512, 512)):
        """
        Initialize COCO downloader.
        
        Args:
            output_dir: Directory to save downloaded datasets
            resize_size: Target size for image resizing
        """
        super().__init__(output_dir, resize_size)
        self.dataset_name = "COCO"
        self.dataset_url = "https://cocodataset.org/#download"
    
    def get_dataset_info(self) -> Dict[str, str]:
        """Get COCO dataset information."""
        return {
            "name": "MS COCO (Common Objects in Context)",
            "description": "Large-scale object detection, segmentation, and captioning dataset",
            "size": "330K images (2017)",
            "content_type": "real",
            "category": "mixed",
            "source": "https://cocodataset.org/"
        }
    
    def download(self) -> Dict[str, any]:
        """
        Download COCO dataset.
        
        Note: COCO requires manual download from official source.
        This method provides instructions and setup.
        
        Returns:
            Dict with download statistics
        """
        print(f"[COCO] Dataset requires manual download from {self.dataset_url}")
        print("[COCO] Please follow these steps:")
        print("1. Visit https://cocodataset.org/#download")
        print("2. Download the 2017 Train/Val images")
        print("3. Extract to the output directory")
        print(f"4. Expected location: {self.output_dir / 'coco'}")
        
        # Create target directories
        for category in ["portrait", "landscape", "object"]:
            target_dir = self.output_dir / "coco" / "images" / "real" / category
            target_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "dataset": "COCO",
            "status": "manual_download_required",
            "instructions": "Manual download required from official source",
            "target_directory": str(self.output_dir / "coco"),
            "downloaded_files": 0
        }

"""
DFDC Dataset Downloader
=======================
Downloader for DeepFake Detection Challenge (DFDC) dataset.
"""

from pathlib import Path
from typing import Dict
from .base_downloader import BaseDownloader


class DFDCDownloader(BaseDownloader):
    """Downloader for DFDC dataset."""
    
    def __init__(self, output_dir: str, resize_size: tuple = (512, 512)):
        """
        Initialize DFDC downloader.
        
        Args:
            output_dir: Directory to save downloaded datasets
            resize_size: Target size for image resizing
        """
        super().__init__(output_dir, resize_size)
        self.dataset_name = "DFDC"
        self.dataset_url = "https://www.kaggle.com/c/deepfake-detection-challenge"
    
    def get_dataset_info(self) -> Dict[str, str]:
        """Get DFDC dataset information."""
        return {
            "name": "DeepFake Detection Challenge (DFDC)",
            "description": "Kaggle deepfake detection challenge dataset with 100K+ videos",
            "size": "100K+ videos",
            "content_type": "ai",
            "category": "portrait",
            "source": "https://www.kaggle.com/c/deepfake-detection-challenge"
        }
    
    def download(self) -> Dict[str, any]:
        """
        Download DFDC dataset.
        
        Note: DFDC requires manual download from Kaggle.
        This method provides instructions and setup.
        
        Returns:
            Dict with download statistics
        """
        print(f"[DFDC] Dataset requires manual download from {self.dataset_url}")
        print("[DFDC] Please follow these steps:")
        print("1. Visit https://www.kaggle.com/c/deepfake-detection-challenge")
        print("2. Accept the competition rules")
        print("3. Download the dataset files")
        print("4. Extract to the output directory")
        print(f"5. Expected location: {self.output_dir / 'dfdc'}")
        
        # Create target directories
        target_dir = self.output_dir / "dfdc" / "videos" / "ai" / "portrait"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "dataset": "DFDC",
            "status": "manual_download_required",
            "instructions": "Manual download required from Kaggle",
            "target_directory": str(self.output_dir / "dfdc"),
            "downloaded_files": 0
        }

"""
FaceForensics++ Dataset Downloader
==================================
Downloader for FaceForensics++ deepfake dataset.
"""

from pathlib import Path
from typing import Dict
from .base_downloader import BaseDownloader


class FaceForensicsDownloader(BaseDownloader):
    """Downloader for FaceForensics++ dataset."""
    
    def __init__(self, output_dir: str, resize_size: tuple = (512, 512)):
        """
        Initialize FaceForensics++ downloader.
        
        Args:
            output_dir: Directory to save downloaded datasets
            resize_size: Target size for image resizing
        """
        super().__init__(output_dir, resize_size)
        self.dataset_name = "FaceForensics++"
        self.dataset_url = "https://github.com/ondyari/FaceForensics"
    
    def get_dataset_info(self) -> Dict[str, str]:
        """Get FaceForensics++ dataset information."""
        return {
            "name": "FaceForensics++",
            "description": "Large-scale deepfake dataset with 1,000 original video sequences",
            "size": "1,000 original videos + 4,000 manipulated",
            "content_type": "ai",
            "category": "portrait",
            "source": "https://github.com/ondyari/FaceForensics"
        }
    
    def download(self) -> Dict[str, any]:
        """
        Download FaceForensics++ dataset.
        
        Note: FaceForensics++ requires manual download from official source.
        This method provides instructions and setup.
        
        Returns:
            Dict with download statistics
        """
        print(f"[FaceForensics++] Dataset requires manual download from {self.dataset_url}")
        print("[FaceForensics++] Please follow these steps:")
        print("1. Visit https://github.com/ondyari/FaceForensics")
        print("2. Download the dataset files")
        print("3. Extract to the output directory")
        print(f"4. Expected location: {self.output_dir / 'faceforensics'}")
        
        # Create target directories
        target_dir = self.output_dir / "faceforensics" / "videos" / "ai" / "portrait"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "dataset": "FaceForensics++",
            "status": "manual_download_required",
            "instructions": "Manual download required from official source",
            "target_directory": str(self.output_dir / "faceforensics"),
            "downloaded_files": 0
        }

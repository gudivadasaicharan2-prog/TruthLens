"""
Base Dataset Downloader
=======================
Abstract base class for dataset downloaders.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, List
import requests
from tqdm import tqdm


class BaseDownloader(ABC):
    """Abstract base class for dataset downloaders."""
    
    def __init__(self, output_dir: str, resize_size: tuple = (512, 512)):
        """
        Initialize downloader.
        
        Args:
            output_dir: Directory to save downloaded datasets
            resize_size: Target size for image resizing (width, height)
        """
        self.output_dir = Path(output_dir)
        self.resize_size = resize_size
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def download(self) -> Dict[str, any]:
        """
        Download dataset.
        
        Returns:
            Dict with download statistics
        """
        pass
    
    @abstractmethod
    def get_dataset_info(self) -> Dict[str, str]:
        """
        Get dataset information.
        
        Returns:
            Dict with dataset metadata
        """
        pass
    
    def download_file(self, url: str, destination: Path, chunk_size: int = 8192) -> bool:
        """
        Download a single file with progress bar.
        
        Args:
            url: URL to download from
            destination: Path to save file
            chunk_size: Download chunk size in bytes
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as f:
                with tqdm(
                    desc=destination.name,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    def verify_download(self, file_path: Path) -> bool:
        """
        Verify downloaded file is not corrupted.
        
        Args:
            file_path: Path to downloaded file
        
        Returns:
            bool: True if file is valid, False otherwise
        """
        if not file_path.exists():
            return False
        
        if file_path.stat().st_size == 0:
            return False
        
        # Try to open image file
        if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    img.verify()
                return True
            except Exception:
                return False
        
        return True

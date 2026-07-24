"""
Image Processor
===============
Handles image resizing and format conversion.
"""

from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
import numpy as np


class ImageProcessor:
    """Process images for dataset preparation."""
    
    def __init__(self, target_size: Tuple[int, int] = (512, 512)):
        """
        Initialize image processor.
        
        Args:
            target_size: Target size for resizing (width, height)
        """
        self.target_size = target_size
    
    def resize_image(self, image_path: Path, output_path: Path) -> bool:
        """
        Resize image to target size.
        
        Args:
            image_path: Path to input image
            output_path: Path to save resized image
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize with high-quality resampling
                img_resized = img.resize(self.target_size, Image.Resampling.LANCZOS)
                
                # Save resized image
                output_path.parent.mkdir(parents=True, exist_ok=True)
                img_resized.save(output_path, 'JPEG', quality=95)
                
                return True
        except Exception as e:
            print(f"Error resizing {image_path}: {e}")
            return False
    
    def batch_resize(self, input_dir: Path, output_dir: Path) -> dict:
        """
        Resize all images in a directory.
        
        Args:
            input_dir: Input directory
            output_dir: Output directory
        
        Returns:
            Dict with processing statistics
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
        processed = 0
        failed = 0
        
        for image_path in input_dir.rglob('*'):
            if image_path.suffix.lower() in image_extensions:
                # Maintain relative path structure
                relative_path = image_path.relative_to(input_dir)
                output_path = output_dir / relative_path
                
                if self.resize_image(image_path, output_path):
                    processed += 1
                else:
                    failed += 1
        
        return {
            "processed": processed,
            "failed": failed,
            "total": processed + failed
        }
    
    def get_image_info(self, image_path: Path) -> Optional[dict]:
        """
        Get image information.
        
        Args:
            image_path: Path to image
        
        Returns:
            Dict with image info or None if error
        """
        try:
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format,
                    "size_bytes": image_path.stat().st_size
                }
        except Exception as e:
            print(f"Error getting info for {image_path}: {e}")
            return None

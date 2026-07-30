"""
Overlay Utilities for TruthLens
================================
Utilities for overlaying heatmaps on original images.
"""

import sys
from pathlib import Path
from typing import Union
import argparse
import numpy as np
from PIL import Image

# Try to import OpenCV for resizing, provide fallback
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


def blend_images(image1: np.ndarray, image2: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """
    Blend two images with given alpha.
    
    Args:
        image1: First image as numpy array (H, W, 3) in [0, 255]
        image2: Second image as numpy array (H, W, 3) in [0, 255]
        alpha: Blending factor (0 = use image1, 1 = use image2)
    
    Returns:
        Blended image as numpy array (H, W, 3) in [0, 255] uint8
    """
    # Ensure both images are in [0, 255] range
    image1 = np.clip(image1, 0, 255).astype(np.float32)
    image2 = np.clip(image2, 0, 255).astype(np.float32)
    
    # Blend: result = (1 - alpha) * image1 + alpha * image2
    blended = (1 - alpha) * image1 + alpha * image2
    
    # Clip to valid range and convert to uint8
    blended = np.clip(blended, 0, 255).astype(np.uint8)
    
    return blended


def resize_to_match(
    source: np.ndarray,
    target_shape: tuple,
    interpolation: str = 'bilinear'
) -> np.ndarray:
    """
    Resize source array to match target shape.
    
    Args:
        source: Source array as numpy array (H, W, C)
        target_shape: Target shape as (height, width)
        interpolation: Interpolation method ('bilinear', 'nearest', 'bicubic')
    
    Returns:
        Resized array as numpy array
    """
    if source.shape[:2] == target_shape:
        return source
    
    if HAS_OPENCV:
        # Map interpolation methods to OpenCV flags
        interp_map = {
            'bilinear': cv2.INTER_LINEAR,
            'nearest': cv2.INTER_NEAREST,
            'bicubic': cv2.INTER_CUBIC
        }
        
        if interpolation not in interp_map:
            raise ValueError(f"Unknown interpolation method: {interpolation}")
        
        # Resize using OpenCV
        resized = cv2.resize(
            source,
            (target_shape[1], target_shape[0]),
            interpolation=interp_map[interpolation]
        )
        return resized
    else:
        # Fallback to PIL
        pil_img = Image.fromarray(source.astype(np.uint8))
        pil_method = {
            'bilinear': Image.BILINEAR,
            'nearest': Image.NEAREST,
            'bicubic': Image.BICUBIC
        }.get(interpolation, Image.BILINEAR)
        
        resized = pil_img.resize((target_shape[1], target_shape[0]), pil_method)
        return np.array(resized)


def overlay_heatmap(
    image: Union[np.ndarray, Image.Image],
    heatmap: np.ndarray,
    alpha: float = 0.5,
    interpolation: str = 'bilinear'
) -> np.ndarray:
    """
    Overlay heatmap on original image.
    
    Args:
        image: Original image as PIL Image or numpy array (H, W, 3) in [0, 255]
        heatmap: Colorized heatmap as numpy array (H, W, 3) in [0, 255]
        alpha: Transparency of heatmap overlay (0 = original, 1 = heatmap only)
        interpolation: Interpolation method for resizing
    
    Returns:
        Overlayed image as numpy array (H, W, 3) in [0, 255] uint8
    """
    # Convert PIL Image to numpy array if needed
    if isinstance(image, Image.Image):
        image = np.array(image)
    
    # Ensure both are numpy arrays
    image = np.asarray(image)
    heatmap = np.asarray(heatmap)
    
    # Ensure both are 3-channel
    if image.ndim == 2:
        image = np.stack([image] * 3, axis=-1)
    if heatmap.ndim == 2:
        heatmap = np.stack([heatmap] * 3, axis=-1)
    
    # Resize heatmap to match image if needed
    if heatmap.shape[:2] != image.shape[:2]:
        heatmap = resize_to_match(heatmap, image.shape[:2], interpolation)
    
    # Blend images
    overlaid = blend_images(image, heatmap, alpha)
    
    return overlaid


def main():
    """CLI entry point for overlay utilities testing."""
    parser = argparse.ArgumentParser(description='Test overlay utilities')
    parser.add_argument(
        '--image-path',
        type=str,
        help='Path to original image'
    )
    parser.add_argument(
        '--heatmap-path',
        type=str,
        help='Path to heatmap image'
    )
    parser.add_argument(
        '--alpha',
        type=float,
        default=0.5,
        help='Blending alpha (0 = original, 1 = heatmap only)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Overlay Utilities Test")
    print("=" * 80)
    
    # Load or generate images
    if args.image_path and Path(args.image_path).exists():
        print(f"\n[Step 1] Loading image from {args.image_path}")
        image = Image.open(args.image_path).convert('RGB')
        image = np.array(image)
    else:
        print("\n[Step 1] Generating dummy image")
        image = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        if args.image_path:
            print(f"[Warning] Image file not found, using dummy data")
    
    if args.heatmap_path and Path(args.heatmap_path).exists():
        print(f"\n[Step 2] Loading heatmap from {args.heatmap_path}")
        heatmap = Image.open(args.heatmap_path).convert('RGB')
        heatmap = np.array(heatmap)
    else:
        print("\n[Step 2] Generating dummy heatmap")
        heatmap = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        if args.heatmap_path:
            print(f"[Warning] Heatmap file not found, using dummy data")
    
    # Print input information
    print("\n[Step 3] Input Information:")
    print("-" * 40)
    print(f"Image shape: {image.shape}")
    print(f"Image dtype: {image.dtype}")
    print(f"Image range: [{image.min()}, {image.max()}]")
    print(f"Heatmap shape: {heatmap.shape}")
    print(f"Heatmap dtype: {heatmap.dtype}")
    print(f"Heatmap range: [{heatmap.min()}, {heatmap.max()}]")
    
    # Overlay
    print(f"\n[Step 4] Overlaying with alpha={args.alpha}")
    overlaid = overlay_heatmap(image, heatmap, alpha=args.alpha)
    
    # Print output information
    print("\n[Step 5] Output Information:")
    print("-" * 40)
    print(f"Output shape: {overlaid.shape}")
    print(f"Output dtype: {overlaid.dtype}")
    print(f"Output range: [{overlaid.min()}, {overlaid.max()}]")
    print(f"Mean value: {overlaid.mean():.2f}")
    print(f"Std deviation: {overlaid.std():.2f}")
    
    print("\n" + "=" * 80)
    print("Overlay Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()


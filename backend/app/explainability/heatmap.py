"""
Heatmap Generation for TruthLens
================================
Utilities for normalizing, resizing, and colorizing heatmaps.
"""

import sys
from pathlib import Path
from typing import Optional
import argparse
import numpy as np

# Try to import OpenCV, provide fallback if not available
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False
    print("[Warning] OpenCV not available. Some colorization features may be limited.")


def normalize_heatmap(heatmap: np.ndarray, method: str = 'minmax') -> np.ndarray:
    """
    Normalize heatmap to [0, 1] range.
    
    Args:
        heatmap: Heatmap as numpy array
        method: Normalization method ('minmax', 'zscore')
    
    Returns:
        Normalized heatmap
    """
    if method == 'minmax':
        if heatmap.max() > heatmap.min():
            return (heatmap - heatmap.min()) / (heatmap.max() - heatmap.min())
        else:
            return np.zeros_like(heatmap)
    elif method == 'zscore':
        mean = heatmap.mean()
        std = heatmap.std()
        if std > 0:
            normalized = (heatmap - mean) / std
            # Clip to reasonable range and rescale to [0, 1]
            normalized = np.clip(normalized, -3, 3)
            return (normalized - normalized.min()) / (normalized.max() - normalized.min())
        else:
            return np.zeros_like(heatmap)
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def resize_heatmap(
    heatmap: np.ndarray,
    target_size: tuple,
    interpolation: str = 'bilinear'
) -> np.ndarray:
    """
    Resize heatmap to target size.
    
    Args:
        heatmap: Heatmap as numpy array (H, W)
        target_size: Target size as (height, width)
        interpolation: Interpolation method ('bilinear', 'nearest', 'bicubic')
    
    Returns:
        Resized heatmap
    """
    if not HAS_OPENCV:
        # Fallback to numpy/scipy-style resize
        from PIL import Image
        pil_img = Image.fromarray((heatmap * 255).astype(np.uint8))
        resized = pil_img.resize((target_size[1], target_size[0]), Image.BILINEAR)
        return np.array(resized).astype(np.float32) / 255.0
    
    # Map interpolation methods to OpenCV flags
    interp_map = {
        'bilinear': cv2.INTER_LINEAR,
        'nearest': cv2.INTER_NEAREST,
        'bicubic': cv2.INTER_CUBIC
    }
    
    if interpolation not in interp_map:
        raise ValueError(f"Unknown interpolation method: {interpolation}")
    
    # Resize using OpenCV
    heatmap_uint8 = (heatmap * 255).astype(np.uint8)
    resized = cv2.resize(
        heatmap_uint8,
        (target_size[1], target_size[0]),
        interpolation=interp_map[interpolation]
    )
    
    return resized.astype(np.float32) / 255.0


def colorize_heatmap(
    heatmap: np.ndarray,
    colormap: int = None
) -> np.ndarray:
    """
    Colorize heatmap using OpenCV colormap.
    
    Args:
        heatmap: Normalized heatmap as numpy array (H, W) in [0, 1]
        colormap: OpenCV colormap constant (default: cv2.COLORMAP_JET)
    
    Returns:
        Colorized heatmap as RGB numpy array (H, W, 3) in [0, 255]
    """
    if not HAS_OPENCV:
        raise ImportError("OpenCV is required for colorization. Install with: pip install opencv-python")
    
    # Set default colormap
    if colormap is None:
        colormap = cv2.COLORMAP_JET
    
    # Convert to uint8 [0, 255]
    heatmap_uint8 = (heatmap * 255).astype(np.uint8)
    
    # Apply colormap
    colored = cv2.applyColorMap(heatmap_uint8, colormap)
    
    # Convert BGR to RGB
    colored_rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    
    return colored_rgb


def generate_heatmap(
    attention_map: np.ndarray,
    normalize: bool = True,
    normalize_method: str = 'minmax',
    resize_to: Optional[tuple] = None,
    colormap: int = None
) -> np.ndarray:
    """
    Generate visualization heatmap from attention map.
    
    Args:
        attention_map: Attention/saliency map as numpy array
        normalize: Whether to normalize the heatmap
        normalize_method: Normalization method ('minmax', 'zscore')
        resize_to: Target size as (height, width) or None
        colormap: OpenCV colormap constant (default: cv2.COLORMAP_JET)
    
    Returns:
        Colorized heatmap as RGB numpy array (H, W, 3) in [0, 255]
    """
    heatmap = attention_map.copy()
    
    # Normalize
    if normalize:
        heatmap = normalize_heatmap(heatmap, method=normalize_method)
    
    # Resize if needed
    if resize_to is not None:
        heatmap = resize_heatmap(heatmap, resize_to)
    
    # Colorize
    colored = colorize_heatmap(heatmap, colormap)
    
    return colored


def main():
    """CLI entry point for heatmap utilities testing."""
    parser = argparse.ArgumentParser(description='Test heatmap utilities')
    parser.add_argument(
        '--heatmap-path',
        type=str,
        help='Path to heatmap numpy file (.npy)'
    )
    parser.add_argument(
        '--size',
        type=int,
        nargs=2,
        default=[224, 224],
        help='Target size for heatmap (height width)'
    )
    parser.add_argument(
        '--colormap',
        type=str,
        default='jet',
        choices=['jet', 'hot', 'cool', 'viridis', 'plasma'],
        help='Colormap name'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("Heatmap Utilities Test")
    print("=" * 80)
    
    # Load or generate heatmap
    if args.heatmap_path and Path(args.heatmap_path).exists():
        print(f"\n[Step 1] Loading heatmap from {args.heatmap_path}")
        heatmap = np.load(args.heatmap_path)
    else:
        print("\n[Step 1] Generating dummy heatmap")
        heatmap = np.random.rand(224, 224)
        if args.heatmap_path:
            print(f"[Warning] Heatmap file not found, using dummy data")
    
    print(f"Input shape: {heatmap.shape}")
    print(f"Input dtype: {heatmap.dtype}")
    print(f"Input range: [{heatmap.min():.4f}, {heatmap.max():.4f}]")
    
    # Normalize
    print("\n[Step 2] Normalizing heatmap")
    normalized = normalize_heatmap(heatmap, method='minmax')
    print(f"Normalized range: [{normalized.min():.4f}, {normalized.max():.4f}]")
    
    # Resize
    print(f"\n[Step 3] Resizing to {tuple(args.size)}")
    resized = resize_heatmap(normalized, tuple(args.size))
    print(f"Resized shape: {resized.shape}")
    
    # Colorize
    print(f"\n[Step 4] Colorizing with {args.colormap} colormap")
    
    if not HAS_OPENCV:
        print("[Error] OpenCV not available. Cannot colorize heatmap.")
        print("Install with: pip install opencv-python")
        return
    
    # Map colormap names to OpenCV constants
    colormap_map = {
        'jet': cv2.COLORMAP_JET,
        'hot': cv2.COLORMAP_HOT,
        'cool': cv2.COLORMAP_COOL,
        'viridis': cv2.COLORMAP_VIRIDIS,
        'plasma': cv2.COLORMAP_PLASMA
    }
    
    colormap = colormap_map.get(args.colormap, cv2.COLORMAP_JET)
    colored = colorize_heatmap(resized, colormap=colormap)
    
    # Report results
    print("\n[Step 5] Results:")
    print("-" * 40)
    print(f"Output shape: {colored.shape}")
    print(f"Output dtype: {colored.dtype}")
    print(f"Output range: [{colored.min()}, {colored.max()}]")
    print(f"Mean value: {colored.mean():.2f}")
    print(f"Std deviation: {colored.std():.2f}")
    
    print("\n" + "=" * 80)
    print("Heatmap Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()


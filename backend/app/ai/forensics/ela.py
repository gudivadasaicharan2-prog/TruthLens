"""
Error Level Analysis (ELA) Forensic Module
===========================================
Detects compression artifacts and image manipulation by re-compressing
the image and comparing error levels.
"""

import io
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance


def ela_score(pil_img: Image.Image) -> tuple[float, float]:
    """
    Error Level Analysis — re-compress at JPEG q=90 and compare.

    Real camera photos re-compressed at the same quality produce low,
    uniform error.  Edited or AI-generated images produce high, uneven error.

    Enhanced with:
    - Edge-specific ELA analysis (AI images often have unnatural edge artifacts)
    - Blockiness detection (JPEG compression vs AI generation patterns)
    - Spatial consistency check

    Returns:
        (ela_var, normalized_score)  where normalized_score is in [0, 1].
    """
    try:
        buf = io.BytesIO()
        pil_img.save(buf, "JPEG", quality=90)
        buf.seek(0)
        resaved = Image.open(buf)
        ela = ImageChops.difference(pil_img, resaved)
        extrema = ela.getextrema()
        max_diff = max(ex[1] for ex in extrema) if extrema else 1
        if max_diff == 0:
            max_diff = 1
        ela = ImageEnhance.Brightness(ela).enhance(255.0 / max_diff)
        ela_arr = np.array(ela)
        gray_ela = cv2.cvtColor(ela_arr, cv2.COLOR_RGB2GRAY)
        ela_var = float(np.var(gray_ela))
        
        # Enhanced: Edge-specific ELA analysis
        # AI-generated images often show higher ELA at edges due to resampling artifacts
        edges = cv2.Canny(gray_ela, 30, 100)
        edge_ratio = float(np.sum(edges > 0) / edges.size) if edges.size > 0 else 0
        
        # Enhanced: Blockiness detection
        # Check for 8x8 block artifacts (JPEG signature) vs irregular patterns (AI)
        h, w = gray_ela.shape
        if h >= 8 and w >= 8:
            # Sample block boundaries
            block_boundary_h = gray_ela[::8, :]
            block_boundary_v = gray_ela[:, ::8]
            block_energy = float(np.mean(block_boundary_h) + np.mean(block_boundary_v))
            # High block energy with low overall variance suggests AI resampling
            block_score = min(max(block_energy / (ela_var + 1e-6), 0.0), 1.0)
        else:
            block_score = 0.0
        
        # Enhanced: Spatial consistency
        # Real photos have more uniform ELA; AI images have hotspots
        ela_mean = float(np.mean(gray_ela))
        ela_std = float(np.std(gray_ela))
        consistency_score = ela_std / (ela_mean + 1e-6) if ela_mean > 0 else 0
        
        # Combine signals
        # Base score from variance
        base_score = min(max((ela_var - 200.0) / 1800.0, 0.0), 1.0)
        
        # Adjust for edge ratio (high edge ELA suggests AI)
        edge_adjustment = edge_ratio * 0.3
        
        # Adjust for blockiness (irregular patterns suggest AI)
        block_adjustment = block_score * 0.2
        
        # Adjust for consistency (high inconsistency suggests AI)
        consistency_adjustment = min(max(consistency_score - 1.0, 0.0), 1.0) * 0.2
        
        final_score = min(max(base_score + edge_adjustment + block_adjustment + consistency_adjustment, 0.0), 1.0)
        
        return ela_var, round(final_score, 4)
    except Exception as e:
        print(f"[ELA] Error: {e}")
        return 0.0, 0.0

"""
Texture Analysis Forensic Module
==================================
Detects GAN/diffusion over-smoothing through patch variance uniformity analysis.
"""

import cv2
import math
import numpy as np


def texture_uniformity_score(gray: np.ndarray) -> float:
    """
    Patch-variance uniformity — detects GAN/diffusion over-smoothing.

    AI-generated images exhibit characteristic spatial uniformity: all image
    regions have similar local variance (smooth backgrounds, uniformly sharp
    subjects).  Real camera images show natural variance differences: blurry
    backgrounds, sharp subjects, varied texture regions.

    Enhanced with:
    - Multi-scale patch analysis (different patch sizes for better detection)
    - Gradient consistency check (AI images have unnatural gradient patterns)
    - Local binary pattern variance (texture richness analysis)

    Returns: float [0, 1] where 1 = suspicious (unnaturally uniform).
    """
    try:
        h, w = gray.shape
        
        # Enhanced: Multi-scale patch analysis
        patch_sizes = [16, 32, 64]
        all_variances = []
        
        for patch_size in patch_sizes:
            if h < patch_size or w < patch_size:
                continue
            variances = []
            step = patch_size // 2  # Overlapping patches for better coverage
            
            for y in range(0, h - patch_size, step):
                for x in range(0, w - patch_size, step):
                    patch = gray[y: y + patch_size, x: x + patch_size]
                    variances.append(float(np.var(patch)))
            
            all_variances.extend(variances)
        
        if len(all_variances) < 8:
            # Fallback to single-scale if multi-scale fails
            patch_size = max(16, min(h, w) // 16)
            variances = []
            for y in range(0, h - patch_size, patch_size):
                for x in range(0, w - patch_size, patch_size):
                    patch = gray[y: y + patch_size, x: x + patch_size]
                    variances.append(float(np.var(patch)))
            all_variances = variances
        
        if len(all_variances) < 4:
            return 0.5

        mean_var = float(np.mean(all_variances))
        if mean_var < 1e-6:
            return 0.90   # completely flat image — strongly suspicious

        var_of_vars = float(np.var(all_variances))
        # Coefficient of variation of patch variances
        cov = math.sqrt(var_of_vars) / (mean_var + 1e-6)

        # Low CoV (< 0.5) → uniform → higher fake score
        # Sigmoid mapping: CoV=0 → 0.88, CoV=0.8 → 0.5, CoV=2.0 → 0.15
        base_score = 1.0 / (1.0 + math.exp((cov - 0.5) * 4.0))
        
        # Enhanced: Gradient consistency check
        # AI images often have unnaturally consistent gradient magnitudes
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Check gradient variance across regions
        h_grad, w_grad = gray.shape
        grad_patches = []
        patch_grad_size = 32
        if h_grad >= patch_grad_size and w_grad >= patch_grad_size:
            for y in range(0, h_grad - patch_grad_size, patch_grad_size):
                for x in range(0, w_grad - patch_grad_size, patch_grad_size):
                    patch = grad_mag[y: y + patch_grad_size, x: x + patch_grad_size]
                    grad_patches.append(float(np.mean(patch)))
            
            if len(grad_patches) >= 4:
                grad_cov = math.sqrt(float(np.var(grad_patches))) / (float(np.mean(grad_patches)) + 1e-6)
                # Low gradient CoV suggests AI uniformity
                if grad_cov < 0.3:
                    gradient_score = 0.3
                elif grad_cov < 0.5:
                    gradient_score = 0.15
                else:
                    gradient_score = 0.0
            else:
                gradient_score = 0.0
        else:
            gradient_score = 0.0
        
        # Enhanced: Local Binary Pattern (LBP) variance
        # Real images have richer texture patterns
        # Simple approximation using local contrast (no scipy dependency)
        if h >= 3 and w >= 3:
            # Compute local contrast using simple 3x3 neighborhood
            # Manual implementation to avoid scipy dependency
            local_contrast = np.zeros_like(gray, dtype=float)
            for y in range(1, h - 1):
                for x in range(1, w - 1):
                    neighborhood = gray[y-1:y+2, x-1:x+2]
                    local_mean = float(np.mean(neighborhood))
                    local_contrast[y, x] = abs(float(gray[y, x]) - local_mean)
            
            contrast_std = float(np.std(local_contrast))
            
            # Low contrast variation suggests AI smoothing
            if contrast_std < 5:
                lbp_score = 0.25
            elif contrast_std < 10:
                lbp_score = 0.1
            else:
                lbp_score = 0.0
        else:
            lbp_score = 0.0
        
        # Combine all signals
        final_score = min(max(base_score + gradient_score + lbp_score, 0.0), 1.0)
        
        return round(final_score, 4)

    except Exception:
        return 0.5

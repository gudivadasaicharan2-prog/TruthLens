"""
Texture Analysis Forensic Module
==================================
Detects GAN/diffusion over-smoothing through patch variance uniformity analysis.
"""

import math
import numpy as np


def texture_uniformity_score(gray: np.ndarray) -> float:
    """
    Patch-variance uniformity — detects GAN/diffusion over-smoothing.

    AI-generated images exhibit characteristic spatial uniformity: all image
    regions have similar local variance (smooth backgrounds, uniformly sharp
    subjects).  Real camera images show natural variance differences: blurry
    backgrounds, sharp subjects, varied texture regions.

    Method:
      1. Divide image into patches (min 16 px, at most 16x16 grid).
      2. Compute local variance of each patch.
      3. Compute the coefficient of variation (std / mean) of those variances.
      4. Low CoV → uniform texture → suspicious AI signal.

    Returns: float [0, 1] where 1 = suspicious (unnaturally uniform).
    """
    try:
        h, w = gray.shape
        patch_size = max(16, min(h, w) // 16)
        variances = []

        for y in range(0, h - patch_size, patch_size):
            for x in range(0, w - patch_size, patch_size):
                patch = gray[y: y + patch_size, x: x + patch_size]
                variances.append(float(np.var(patch)))

        if len(variances) < 4:
            return 0.5

        mean_var = float(np.mean(variances))
        if mean_var < 1e-6:
            return 0.90   # completely flat image — strongly suspicious

        var_of_vars = float(np.var(variances))
        # Coefficient of variation of patch variances
        cov = math.sqrt(var_of_vars) / (mean_var + 1e-6)

        # Low CoV (< 0.5) → uniform → higher fake score
        # Sigmoid mapping: CoV=0 → 0.88, CoV=0.8 → 0.5, CoV=2.0 → 0.15
        score = 1.0 / (1.0 + math.exp((cov - 0.5) * 4.0))
        return round(min(max(score, 0.0), 1.0), 4)

    except Exception:
        return 0.5

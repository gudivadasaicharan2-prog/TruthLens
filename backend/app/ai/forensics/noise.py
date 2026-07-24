"""
Noise Analysis Forensic Module
===============================
Detects quadrant noise variance inconsistencies that indicate splicing
or compositing operations.
"""

import cv2
import numpy as np


def noise_splice_score(gray: np.ndarray) -> tuple[float, float]:
    """
    Quadrant noise-variance — measures inconsistency in sensor noise across
    image regions. High variance of quadrant stds signals splicing/compositing.

    Enhanced with:
    - 9-grid analysis (more granular than 4 quadrants)
    - Natural sensor noise pattern detection (Poisson-like distribution)
    - High-frequency noise analysis (sensor noise vs AI smoothness)

    Returns:
        (noise_var, normalized_score) where normalized_score is in [0, 1].
    """
    try:
        h, w = gray.shape
        
        # Enhanced: 9-grid analysis for better localization
        grid_h, grid_w = 3, 3
        h_step, w_step = h // grid_h, w // grid_w
        regions = []
        for i in range(grid_h):
            for j in range(grid_w):
                y_start, y_end = i * h_step, (i + 1) * h_step if i < grid_h - 1 else h
                x_start, x_end = j * w_step, (j + 1) * w_step if j < grid_w - 1 else w
                regions.append(gray[y_start:y_end, x_start:x_end])
        
        stds = [float(np.std(r)) for r in regions]
        noise_var = float(np.var(stds))
        
        # Enhanced: Natural sensor noise pattern detection
        # Real sensor noise follows approximately Poisson distribution
        # AI-generated images often have unnaturally uniform or Gaussian noise
        if len(stds) >= 4:
            # Check for natural variance in noise levels
            std_mean = float(np.mean(stds))
            std_std = float(np.std(stds))
            # Natural sensor noise has some variation but not extreme
            naturalness_score = 0.0
            if std_mean > 0:
                cv = std_std / std_mean
                # CV between 0.1 and 0.4 is typical for natural sensor noise
                if cv < 0.05:  # Too uniform - suspicious
                    naturalness_score = 0.4
                elif cv > 0.6:  # Too variable - splicing
                    naturalness_score = 0.6
                else:
                    naturalness_score = 0.1
        else:
            naturalness_score = 0.0
        
        # Enhanced: High-frequency noise analysis
        # Real photos have natural high-frequency sensor noise
        # AI images often have smoothed high frequencies
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        hf_noise = float(np.std(laplacian))
        # Very low high-frequency noise suggests AI smoothing
        hf_score = 0.0
        if hf_noise < 5:
            hf_score = 0.5
        elif hf_noise < 10:
            hf_score = 0.2
        
        # Base score from quadrant variance
        base_score = min(max((noise_var - 5.0) / 45.0, 0.0), 1.0)
        
        # Combine signals
        final_score = min(max(base_score + naturalness_score + hf_score, 0.0), 1.0)
        
        return noise_var, round(final_score, 4)
    except Exception:
        return 0.0, 0.0

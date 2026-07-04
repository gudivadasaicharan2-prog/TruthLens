"""
Noise Analysis Forensic Module
===============================
Detects quadrant noise variance inconsistencies that indicate splicing
or compositing operations.
"""

import numpy as np


def noise_splice_score(gray: np.ndarray) -> tuple[float, float]:
    """
    Quadrant noise-variance — measures inconsistency in sensor noise across
    image regions. High variance of quadrant stds signals splicing/compositing.

    Returns:
        (noise_var, normalized_score) where normalized_score is in [0, 1].
    """
    try:
        h, w = gray.shape
        quads = [
            gray[:h//2, :w//2], gray[:h//2, w//2:],
            gray[h//2:, :w//2], gray[h//2:, w//2:],
        ]
        stds = [float(np.std(q)) for q in quads]
        noise_var = float(np.var(stds))
        # Normalise: < 5 is clean; > 50 is strongly suspicious
        score = min(max((noise_var - 5.0) / 45.0, 0.0), 1.0)
        return noise_var, round(score, 4)
    except Exception:
        return 0.0, 0.0

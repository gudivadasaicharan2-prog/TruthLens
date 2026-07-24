"""
Color Analysis Forensic Module
===============================
Detects color channel correlation anomalies and hue flatness.
"""

import numpy as np
import cv2


def color_channel_anomaly(img_array: np.ndarray) -> float:
    """
    Color channel correlation anomaly detection.

    Real camera images have a characteristic R-B channel correlation
    (~0.65–0.92) imposed by natural scene statistics and Bayer demosaicing.
    AI-generated images often have near-perfect correlation (over-stylised)
    or unusual correlation structures.

    Enhanced with:
    - Multi-channel correlation analysis (R-G, G-B, R-B)
    - Saturation distribution analysis (AI images often have unnatural saturation)
    - Color histogram uniformity (AI images have more uniform color distributions)

    Returns: float [0, 1] where 1 = suspicious.
    """
    try:
        r = img_array[:, :, 0].astype(np.float32).flatten()
        g = img_array[:, :, 1].astype(np.float32).flatten()
        b = img_array[:, :, 2].astype(np.float32).flatten()

        # Subsample for speed on large arrays
        step = max(1, len(r) // 10000)
        r_s, g_s, b_s = r[::step], g[::step], b[::step]

        # Enhanced: Multi-channel correlation analysis
        correlations = []
        for ch1, ch2 in [(r_s, g_s), (g_s, b_s), (r_s, b_s)]:
            if np.std(ch1) > 1e-5 and np.std(ch2) > 1e-5:
                corr = float(np.corrcoef(ch1, ch2)[0, 1])
                correlations.append(corr)
        
        if len(correlations) == 0:
            corr_score = 0.50
        else:
            avg_corr = float(np.mean(correlations))
            # Natural range: ~0.65–0.92; suspicious if outside
            if avg_corr > 0.97 or avg_corr < 0.35:
                corr_score = 0.72
            elif avg_corr > 0.94 or avg_corr < 0.50:
                corr_score = 0.40
            else:
                corr_score = 0.12
        
        # Enhanced: Saturation distribution analysis
        # AI images often have unnaturally high or uniform saturation
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        saturation = hsv[:, :, 1].astype(np.float32).flatten()
        sat_mean = float(np.mean(saturation))
        sat_std = float(np.std(saturation))
        
        # Check for unnatural saturation patterns
        sat_score = 0.0
        if sat_mean > 180:  # Oversaturated (common in AI art)
            sat_score = 0.35
        elif sat_std < 15 and sat_mean > 50:  # Uniform saturation with high mean
            sat_score = 0.25
        elif sat_std < 8:  # Very uniform saturation
            sat_score = 0.15
        
        # Enhanced: Color histogram uniformity
        # AI images often have more uniform color distributions
        # Real photos have natural peaks and valleys
        hist_r = cv2.calcHist([img_array], [0], None, [32], [0, 256])
        hist_g = cv2.calcHist([img_array], [1], None, [32], [0, 256])
        hist_b = cv2.calcHist([img_array], [2], None, [32], [0, 256])
        
        # Normalize histograms
        hist_r = hist_r / (np.sum(hist_r) + 1e-6)
        hist_g = hist_g / (np.sum(hist_g) + 1e-6)
        hist_b = hist_b / (np.sum(hist_b) + 1e-6)
        
        # Measure histogram entropy (uniformity)
        def entropy(hist):
            hist = hist[hist > 0]
            return -np.sum(hist * np.log2(hist + 1e-6))
        
        ent_r = entropy(hist_r)
        ent_g = entropy(hist_g)
        ent_b = entropy(hist_b)
        avg_entropy = float(np.mean([ent_r, ent_g, ent_b]))
        
        # High entropy = uniform distribution = suspicious
        # Natural images have entropy around 3.5-4.5
        hist_score = 0.0
        if avg_entropy > 4.8:
            hist_score = 0.3
        elif avg_entropy > 4.5:
            hist_score = 0.15
        
        # Original hue check (kept for backward compatibility)
        hue_std = float(np.std(hsv[:, :, 0]))
        hue_score = 0.30 if hue_std < 7 else 0.05

        # Combine all signals
        final_score = round((corr_score * 0.4 + sat_score * 0.25 + hist_score * 0.2 + hue_score * 0.15), 4)

        return final_score

    except Exception:
        return 0.5

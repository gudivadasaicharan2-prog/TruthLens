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

    Additionally, we check for unnaturally low hue variation, which is a
    known signature of some GAN architectures.

    Returns: float [0, 1] where 1 = suspicious.
    """
    try:
        r = img_array[:, :, 0].astype(np.float32).flatten()
        b = img_array[:, :, 2].astype(np.float32).flatten()

        # Subsample for speed on large arrays
        step = max(1, len(r) // 10000)
        r_s, b_s = r[::step], b[::step]

        if np.std(r_s) < 1e-5 or np.std(b_s) < 1e-5:
            corr_score = 0.50
        else:
            rb_corr = float(np.corrcoef(r_s, b_s)[0, 1])

            # Natural range: ~0.65–0.92; suspicious if outside
            if rb_corr > 0.97 or rb_corr < 0.35:
                corr_score = 0.72
            elif rb_corr > 0.94 or rb_corr < 0.50:
                corr_score = 0.40
            else:
                corr_score = 0.12

        # Hue-channel standard deviation — AI images sometimes unnaturally flat
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        hue_std = float(np.std(hsv[:, :, 0]))
        hue_score = 0.60 if hue_std < 7 else 0.10

        return round((corr_score * 0.6 + hue_score * 0.4), 4)

    except Exception:
        return 0.5

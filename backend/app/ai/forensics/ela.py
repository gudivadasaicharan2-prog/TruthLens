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
        # Normalise: < 200 is clean; > 2000 is strongly anomalous
        score = min(max((ela_var - 200.0) / 1800.0, 0.0), 1.0)
        return ela_var, round(score, 4)
    except Exception as e:
        print(f"[ELA] Error: {e}")
        return 0.0, 0.0

"""
Metadata and EXIF Analysis Forensic Module
===========================================
Extracts and analyzes EXIF metadata for camera authenticity.
"""

from PIL import Image
from PIL.ExifTags import TAGS


def extract_exif(image_path: str) -> dict:
    """Extract EXIF tags from a JPEG/TIFF image. Returns empty dict on failure."""
    try:
        img = Image.open(image_path)
        raw = img._getexif()
        if not raw:
            return {}
        return {TAGS.get(k, k): str(v) for k, v in raw.items()}
    except Exception:
        return {}


def get_device_name(exif: dict) -> str:
    make  = exif.get("Make", "")
    model = exif.get("Model", "")
    if make and model:
        return f"{make.strip()} {model.strip()}"
    return make or model or "Unknown"


def exif_authenticity_score(exif: dict) -> float:
    """
    Score EXIF completeness and consistency for camera authenticity.

    Real cameras write: Make, Model, ExposureTime, FNumber, ISOSpeedRatings,
    DateTime, and lens data — all together.  AI tools either produce empty
    EXIF or write only a 'Software' tag.

    Returns: float [0, 1] where 1 = authentic-looking, 0 = suspicious.
    """
    if not exif:
        # No EXIF — neutral (many real web images strip EXIF too)
        return 0.40

    # AI software keywords in EXIF Software tag = strong indicator
    software = exif.get("Software", "").lower()
    ai_sw_keywords = [
        "midjourney", "dall-e", "stable diffusion", "firefly", "adobe firefly",
        "generative", "ai generated", "nightcafe", "artbreeder",
    ]
    if any(kw in software for kw in ai_sw_keywords):
        return 0.05   # near-certain AI

    # Score based on presence of real camera EXIF fields
    camera_fields = {"Make", "Model", "ExposureTime", "FNumber", "ISOSpeedRatings"}
    present = sum(1 for f in camera_fields if f in exif)

    if present >= 4:
        return 0.95
    elif present >= 2:
        return 0.70
    elif present >= 1:
        return 0.45
    else:
        return 0.25   # has EXIF but no camera fields — suspicious

"""
Image Type Classifier
====================
Lightweight computer-vision heuristics for image type classification.
Uses existing libraries (cv2, numpy, PIL) - no new dependencies.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, Tuple


def _detect_edges(gray: np.ndarray) -> float:
    """Calculate edge density using Canny edge detection."""
    edges = cv2.Canny(gray, 50, 150)
    return float(np.sum(edges > 0) / edges.size)


def _detect_text_regions(gray: np.ndarray) -> float:
    """Detect text-like regions using morphological operations."""
    # Use MSER for text-like region detection
    mser = cv2.MSER_create()
    regions, _ = mser.detectRegions(gray)
    return float(len(regions))


def _analyze_color_distribution(img_array: np.ndarray) -> Dict[str, float]:
    """Analyze color distribution for artwork/cartoon detection."""
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    
    # Saturation analysis
    saturation = hsv[:, :, 1]
    avg_saturation = float(np.mean(saturation))
    high_sat_ratio = float(np.sum(saturation > 150) / saturation.size)
    
    # Hue variance
    hue = hsv[:, :, 0]
    hue_std = float(np.std(hue))
    
    return {
        "avg_saturation": avg_saturation,
        "high_sat_ratio": high_sat_ratio,
        "hue_std": hue_std
    }


def _analyze_aspect_ratio(width: int, height: int) -> str:
    """Determine orientation from aspect ratio."""
    ratio = width / height if height > 0 else 1.0
    
    if ratio < 0.8:
        return "portrait"
    elif ratio > 1.2:
        return "landscape"
    else:
        return "square"


def _is_screenshot(gray: np.ndarray, img_array: np.ndarray) -> bool:
    """Detect screenshots based on edge patterns and uniform regions."""
    edge_density = _detect_edges(gray)
    
    # Screenshots often have high edge density from UI elements
    # and relatively uniform backgrounds
    if edge_density > 0.15:
        # Check for rectangular regions (UI windows)
        contours, _ = cv2.findContours(
            cv2.Canny(gray, 50, 150),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        rect_count = sum(1 for c in contours if len(cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)) == 4)
        
        if rect_count > 3:
            return True
    
    return False


def _is_document(gray: np.ndarray, img_array: np.ndarray) -> bool:
    """Detect documents based on text regions and aspect ratio."""
    text_regions = _detect_text_regions(gray)
    edge_density = _detect_edges(gray)
    
    # Documents have high text region count and moderate edge density
    if text_regions > 50 and edge_density > 0.1:
        return True
    
    return False


def _is_artwork_or_cartoon(img_array: np.ndarray, color_stats: Dict[str, float]) -> Tuple[str, bool]:
    """Distinguish between artwork, AI artwork, and cartoons."""
    # High saturation and high hue variance suggest artwork
    if color_stats["high_sat_ratio"] > 0.3 and color_stats["hue_std"] > 30:
        # Check for smooth gradients (AI artwork characteristic)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(gradient_x**2 + gradient_y**2)
        gradient_std = float(np.std(gradient_mag))
        
        if gradient_std < 20:  # Very smooth gradients
            return "ai_artwork", True
        else:
            return "artwork", True
    
    # Lower saturation with high hue variance suggests cartoon
    if color_stats["avg_saturation"] < 80 and color_stats["hue_std"] > 40:
        return "cartoon", True
    
    return "unknown", False


def classify_image_type(
    img_array: np.ndarray,
    face_count: int = 0
) -> Dict[str, any]:
    """
    Classify image type using lightweight CV heuristics.
    
    Args:
        img_array: RGB image as numpy array
        face_count: Number of faces detected (from face detector)
    
    Returns:
        Dict with keys:
            - image_type: str (one of the 10 types)
            - contains_faces: bool
            - face_count: int
            - recommended_pipeline: "face" | "whole_image" | "document"
    """
    height, width = img_array.shape[:2]
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Basic analysis
    aspect_ratio_type = _analyze_aspect_ratio(width, height)
    edge_density = _detect_edges(gray)
    color_stats = _analyze_color_distribution(img_array)
    
    # Special type detection
    is_screenshot = _is_screenshot(gray, img_array)
    is_document = _is_document(gray, img_array)
    
    # Determine image type
    image_type = "mixed_scene"
    
    if is_screenshot:
        image_type = "screenshot"
    elif is_document:
        image_type = "document"
    elif face_count > 0:
        # Determine between portrait and selfie based on aspect ratio
        if aspect_ratio_type == "portrait":
            image_type = "portrait" if face_count == 1 else "selfie"
        else:
            image_type = "portrait" if face_count == 1 else "selfie"
    else:
        # No faces - check for artwork/cartoon/object
        artwork_type, is_artwork = _is_artwork_or_cartoon(img_array, color_stats)
        if is_artwork:
            image_type = artwork_type
        elif edge_density < 0.05:
            # Very low edge density - likely simple object
            image_type = "object"
        elif aspect_ratio_type == "landscape":
            image_type = "landscape"
    
    # Determine recommended pipeline
    if image_type in ["document", "screenshot"]:
        recommended_pipeline = "document"
    elif image_type in ["portrait", "selfie"] and face_count > 0:
        recommended_pipeline = "face"
    else:
        recommended_pipeline = "whole_image"
    
    return {
        "image_type": image_type,
        "contains_faces": face_count > 0,
        "face_count": face_count,
        "recommended_pipeline": recommended_pipeline
    }

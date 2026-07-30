"""
Image Type Classifier
====================
Enhanced computer-vision heuristics for image type classification with confidence scores.
Uses existing libraries (cv2, numpy, PIL) - no new dependencies.
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, Tuple, Optional
import math


def _detect_edges(gray: np.ndarray) -> float:
    """Calculate edge density using Canny edge detection."""
    edges = cv2.Canny(gray, 50, 150)
    return float(np.sum(edges > 0) / edges.size)


def _detect_text_regions(gray: np.ndarray) -> float:
    """Detect text-like regions using morphological operations."""
    try:
        mser = cv2.MSER_create()
        regions, _ = mser.detectRegions(gray)
        return float(len(regions))
    except:
        return 0.0


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
    
    # Brightness distribution
    value = hsv[:, :, 2]
    brightness_std = float(np.std(value))
    
    return {
        "avg_saturation": avg_saturation,
        "high_sat_ratio": high_sat_ratio,
        "hue_std": hue_std,
        "brightness_std": brightness_std
    }


def _analyze_aspect_ratio(width: int, height: int) -> Tuple[str, float]:
    """Determine orientation from aspect ratio with confidence."""
    ratio = width / height if height > 0 else 1.0
    
    if ratio < 0.8:
        confidence = 1.0 - (ratio / 0.8)
        return "portrait", min(confidence, 0.95)
    elif ratio > 1.2:
        confidence = 1.0 - (1.2 / ratio)
        return "landscape", min(confidence, 0.95)
    else:
        # Near square - lower confidence
        confidence = 1.0 - abs(ratio - 1.0) * 2
        return "square", max(confidence, 0.5)


def _calculate_texture_entropy(gray: np.ndarray) -> float:
    """Calculate texture entropy using local binary patterns approximation."""
    # Simple entropy calculation using histogram
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist / np.sum(hist)
    entropy = -np.sum(hist * np.log2(hist + 1e-10))
    return float(entropy)


def _detect_compression_artifacts(img_array: np.ndarray) -> float:
    """Detect JPEG compression artifacts using blockiness detection."""
    try:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    except:
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    
    # Detect horizontal block boundaries (8x8 blocks)
    # Handle images where width/height is not divisible by 8
    h_diff = np.array([])
    v_diff = np.array([])
    
    try:
        h_start = gray[:, 8::8]
        h_end = gray[:, 7::8]
        min_h_width = min(h_start.shape[1], h_end.shape[1])
        h_diff = np.abs(h_start[:, :min_h_width] - h_end[:, :min_h_width])
    except:
        pass
    
    try:
        v_start = gray[8::8, :]
        v_end = gray[7::8, :]
        min_v_height = min(v_start.shape[0], v_end.shape[0])
        v_diff = np.abs(v_start[:min_v_height, :] - v_end[:min_v_height, :])
    except:
        pass
    
    blockiness = 0.0
    if h_diff.size > 0:
        blockiness += float(np.mean(h_diff))
    if v_diff.size > 0:
        blockiness += float(np.mean(v_diff))
    
    return blockiness


def _detect_sensor_noise(gray: np.ndarray) -> float:
    """Estimate sensor noise in flat regions."""
    # Use standard deviation in low-variance regions
    kernel = np.ones((5, 5), np.float32) / 25
    local_var = cv2.filter2D(gray.astype(np.float32), -1, kernel)
    noise_estimate = float(np.std(gray[local_var < 50])) if np.any(local_var < 50) else 0.0
    return noise_estimate


def _detect_illustration_edges(gray: np.ndarray) -> float:
    """Detect illustration-like edges (smooth, cartoon-like)."""
    # Use adaptive thresholding to find clean edges
    edges = cv2.Canny(gray, 50, 150)
    
    # Check edge smoothness - illustrations have cleaner edges
    kernel = np.ones((3, 3), np.float32) / 9
    smooth_edges = cv2.filter2D(edges.astype(np.float32), -1, kernel)
    edge_smoothness = float(np.mean(smooth_edges > 100))
    
    return edge_smoothness


def _detect_diffusion_patterns(img_array: np.ndarray) -> float:
    """Detect diffusion-style color transitions (AI artwork characteristic)."""
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    
    # Check for smooth color gradients in hue channel
    hue = hsv[:, :, 0].astype(np.float32)
    gradient_x = cv2.Sobel(hue, cv2.CV_64F, 1, 0, ksize=5)
    gradient_y = cv2.Sobel(hue, cv2.CV_64F, 0, 1, ksize=5)
    gradient_mag = np.sqrt(gradient_x**2 + gradient_y**2)
    
    # Low gradient magnitude indicates smooth transitions
    smoothness = 1.0 - min(float(np.mean(gradient_mag)) / 50.0, 1.0)
    return smoothness


def _is_screenshot(gray: np.ndarray, img_array: np.ndarray) -> Tuple[bool, float]:
    """Detect screenshots based on edge patterns and uniform regions with confidence."""
    edge_density = _detect_edges(gray)
    text_regions = _detect_text_regions(gray)
    
    confidence = 0.0
    
    # Screenshots often have high edge density from UI elements
    if edge_density > 0.15:
        confidence += 0.4
        
        # Check for rectangular regions (UI windows)
        contours, _ = cv2.findContours(
            cv2.Canny(gray, 50, 150),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        rect_count = sum(1 for c in contours if len(cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)) == 4)
        
        if rect_count > 3:
            confidence += 0.4
    
    # Check for text regions (UI text)
    if text_regions > 30:
        confidence += 0.2
    
    # Check for compression artifacts (screenshots often compressed)
    compression = _detect_compression_artifacts(img_array)
    if compression > 5:
        confidence += 0.1
    
    return confidence > 0.6, min(confidence, 0.95)


def _is_document(gray: np.ndarray, img_array: np.ndarray) -> Tuple[bool, float]:
    """Detect documents based on text regions and aspect ratio with confidence."""
    text_regions = _detect_text_regions(gray)
    edge_density = _detect_edges(gray)
    
    confidence = 0.0
    
    # Documents have high text region count
    if text_regions > 50:
        confidence += 0.5
        confidence += min((text_regions - 50) / 100, 0.3)
    
    # Moderate edge density (text edges)
    if 0.1 < edge_density < 0.3:
        confidence += 0.2
    
    # Check for white/light background
    gray_mean = float(np.mean(gray))
    if gray_mean > 180:
        confidence += 0.1
    
    # Check aspect ratio (documents often portrait or A4-like)
    height, width = img_array.shape[:2]
    ratio = width / height if height > 0 else 1.0
    if 0.6 < ratio < 0.85:  # Portrait document
        confidence += 0.1
    
    return confidence > 0.6, min(confidence, 0.95)


def _is_ai_artwork(img_array: np.ndarray, color_stats: Dict[str, float]) -> Tuple[bool, float]:
    """Detect AI artwork using multiple heuristics with confidence."""
    confidence = 0.0
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Check 1: Smooth gradients (diffusion characteristic)
    diffusion_smoothness = _detect_diffusion_patterns(img_array)
    if diffusion_smoothness > 0.7:
        confidence += 0.3
        confidence += (diffusion_smoothness - 0.7) * 0.3
    
    # Check 2: Low sensor noise (AI images lack sensor noise)
    sensor_noise = _detect_sensor_noise(gray)
    if sensor_noise < 5:
        confidence += 0.2
        confidence += (5 - sensor_noise) / 25
    
    # Check 3: Painterly color transitions
    if color_stats["high_sat_ratio"] > 0.3 and color_stats["hue_std"] > 30:
        confidence += 0.2
    
    # Check 4: Illustration-like edges
    illustration_edges = _detect_illustration_edges(gray)
    if illustration_edges > 0.3:
        confidence += 0.1
    
    # Check 5: Uniform smooth textures
    gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_mag = np.sqrt(gradient_x**2 + gradient_y**2)
    gradient_std = float(np.std(gradient_mag))
    if gradient_std < 25:
        confidence += 0.2
    
    return confidence > 0.6, min(confidence, 0.98)


def _is_cartoon(img_array: np.ndarray, color_stats: Dict[str, float]) -> Tuple[bool, float]:
    """Detect cartoons/illustrations with confidence."""
    confidence = 0.0
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Lower saturation with high hue variance suggests cartoon
    if color_stats["avg_saturation"] < 80 and color_stats["hue_std"] > 40:
        confidence += 0.4
        confidence += (color_stats["hue_std"] - 40) / 100
    
    # Clean edges (cartoons have sharp, clean edges)
    edge_density = _detect_edges(gray)
    if 0.1 < edge_density < 0.25:
        confidence += 0.3
    
    # Low texture entropy (flat colors)
    entropy = _calculate_texture_entropy(gray)
    if entropy < 6:
        confidence += 0.2
    
    # Illustration-like edge patterns
    illustration_edges = _detect_illustration_edges(gray)
    if illustration_edges > 0.4:
        confidence += 0.1
    
    return confidence > 0.6, min(confidence, 0.95)


def _is_artwork(img_array: np.ndarray, color_stats: Dict[str, float]) -> Tuple[bool, float]:
    """Detect traditional artwork with confidence."""
    confidence = 0.0
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # High saturation and high hue variance suggest artwork
    if color_stats["high_sat_ratio"] > 0.3 and color_stats["hue_std"] > 30:
        confidence += 0.4
        confidence += (color_stats["high_sat_ratio"] - 0.3) * 0.3
    
    # Moderate edge density (brush strokes)
    edge_density = _detect_edges(gray)
    if 0.08 < edge_density < 0.2:
        confidence += 0.2
    
    # Higher texture entropy (paint texture)
    entropy = _calculate_texture_entropy(gray)
    if 6 < entropy < 8:
        confidence += 0.2
    
    # Some sensor noise (traditional medium)
    sensor_noise = _detect_sensor_noise(gray)
    if 5 < sensor_noise < 15:
        confidence += 0.2
    
    return confidence > 0.6, min(confidence, 0.95)


def _is_real_photograph(img_array: np.ndarray, color_stats: Dict[str, float], 
                        edge_density: float, face_count: int) -> Tuple[bool, float]:
    """Detect real photographs with confidence."""
    confidence = 0.0
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Natural color distribution
    if 80 < color_stats["avg_saturation"] < 140 and color_stats["hue_std"] < 50:
        confidence += 0.3
    
    # Moderate edge density (natural scenes)
    if 0.05 < edge_density < 0.15:
        confidence += 0.2
    
    # Sensor noise present
    sensor_noise = _detect_sensor_noise(gray)
    if sensor_noise > 5:
        confidence += 0.2
        confidence += min(sensor_noise / 30, 0.1)
    
    # Compression artifacts (real photos often compressed)
    compression = _detect_compression_artifacts(img_array)
    if compression > 3:
        confidence += 0.1
    
    # Texture entropy (natural textures)
    entropy = _calculate_texture_entropy(gray)
    if entropy > 7:
        confidence += 0.1
    
    # Faces present (common in photos)
    if face_count > 0:
        confidence += 0.1
    
    return confidence > 0.5, min(confidence, 0.92)


def _is_object(img_array: np.ndarray, edge_density: float, 
               aspect_ratio_type: str) -> Tuple[bool, float]:
    """Detect simple objects with confidence."""
    confidence = 0.0
    
    # Very low edge density
    if edge_density < 0.05:
        confidence += 0.5
        confidence += (0.05 - edge_density) * 10
    
    # Square aspect ratio (common for objects)
    if aspect_ratio_type == "square":
        confidence += 0.3
    
    # Low texture complexity
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    entropy = _calculate_texture_entropy(gray)
    if entropy < 5:
        confidence += 0.2
    
    return confidence > 0.6, min(confidence, 0.90)


def classify_image_type(
    img_array: np.ndarray,
    face_count: int = 0
) -> Dict[str, any]:
    """
    Classify image type using enhanced CV heuristics with confidence scores.
    
    Args:
        img_array: RGB image as numpy array
        face_count: Number of faces detected (from face detector)
    
    Returns:
        Dict with keys:
            - image_type: str (one of the 10+ types)
            - image_type_confidence: float (0-1)
            - recommended_pipeline: str
            - contains_faces: bool
            - face_count: int
            - heuristics: dict (detailed heuristic scores)
    """
    height, width = img_array.shape[:2]
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Enhanced analysis
    aspect_ratio_type, aspect_confidence = _analyze_aspect_ratio(width, height)
    edge_density = _detect_edges(gray)
    color_stats = _analyze_color_distribution(img_array)
    texture_entropy = _calculate_texture_entropy(gray)
    sensor_noise = _detect_sensor_noise(gray)
    compression_artifacts = _detect_compression_artifacts(img_array)
    
    # Collect all heuristics
    heuristics = {
        "edge_density": edge_density,
        "aspect_ratio": width / height if height > 0 else 1.0,
        "avg_saturation": color_stats["avg_saturation"],
        "hue_std": color_stats["hue_std"],
        "texture_entropy": texture_entropy,
        "sensor_noise": sensor_noise,
        "compression_artifacts": compression_artifacts,
        "face_count": face_count
    }
    
    # Special type detection with confidence
    is_screenshot, screenshot_conf = _is_screenshot(gray, img_array)
    is_document, document_conf = _is_document(gray, img_array)
    is_ai_artwork, ai_artwork_conf = _is_ai_artwork(img_array, color_stats)
    is_cartoon, cartoon_conf = _is_cartoon(img_array, color_stats)
    is_artwork, artwork_conf = _is_artwork(img_array, color_stats)
    is_real_photo, photo_conf = _is_real_photograph(img_array, color_stats, edge_density, face_count)
    is_object, object_conf = _is_object(img_array, edge_density, aspect_ratio_type)
    
    # Determine image type with confidence
    type_candidates = []
    
    if is_screenshot:
        type_candidates.append(("screenshot", screenshot_conf))
    if is_document:
        type_candidates.append(("document", document_conf))
    if is_ai_artwork:
        type_candidates.append(("ai_artwork", ai_artwork_conf))
    if is_cartoon:
        type_candidates.append(("cartoon", cartoon_conf))
    if is_artwork:
        type_candidates.append(("artwork", artwork_conf))
    
    # Face-based classification
    if face_count > 0:
        if face_count == 1:
            type_candidates.append(("portrait", 0.85))
        else:
            type_candidates.append(("selfie", 0.85))
    
    if is_real_photo:
        type_candidates.append(("real_photograph", photo_conf))
    if is_object:
        type_candidates.append(("object", object_conf))
    
    # Default to mixed scene if no strong candidates
    if not type_candidates:
        type_candidates.append(("mixed_scene", 0.5))
    
    # Select highest confidence type
    image_type, confidence = max(type_candidates, key=lambda x: x[1])
    
    # Determine recommended pipeline
    if image_type in ["document", "screenshot"]:
        recommended_pipeline = "document"
    elif image_type in ["portrait", "selfie"]:
        recommended_pipeline = "portrait" if face_count == 1 else "selfie"
    elif image_type in ["ai_artwork", "artwork", "cartoon"]:
        recommended_pipeline = "artwork"
    elif image_type == "object":
        recommended_pipeline = "object"
    else:
        recommended_pipeline = "photo"
    
    return {
        "image_type": image_type,
        "image_type_confidence": round(confidence, 3),
        "recommended_pipeline": recommended_pipeline,
        "contains_faces": face_count > 0,
        "face_count": face_count,
        "heuristics": heuristics
    }

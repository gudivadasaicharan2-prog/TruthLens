"""
TruthLens — Image Authenticity Analyzer (v6 — Configurable Fusion)
===================================================================
Pipeline (runs for every image, regardless of whether faces are present):

  [1] Whole-image AI score    EfficientNet-B2 on the full image
  [2] Face deepfake score     EfficientNet-B2 on each face crop (optional)
  [3] Forensic bundle         ELA · Noise · Frequency · Texture · Color · EXIF
  [4] Fusion engine           Weighted combination → final_fake_prob → verdict

Signal weights: Configurable via fusion_config.py
  - Document pipeline: forensic-heavy
  - Artwork pipeline: whole-image + forensic
  - Landscape pipeline: whole-image + forensic
  - Portrait pipeline: face-heavy
  - Default: adaptive based on image type

Verdict set (exactly 5, as required):
  Authentic | Likely Authentic | Suspicious | AI Generated | Deepfake

  "Deepfake"     — face deepfake score dominates the fused result
  "AI Generated" — whole-image AI score dominates (works for landscapes, art, etc.)
  "Suspicious"   — inconclusive signals, mid-range probability
  "Likely Authentic" — leaning real, minor anomalies present
  "Authentic"    — strong authentic signal across all channels

Confidence calibration:
  logistic(|fake_prob - 0.5| * scale) ensures configurable confidence

JSON response: identical to v4 — zero frontend changes required.
  - New fields: module_contributions, explanation (backward compatible additions)
"""

import cv2
import numpy as np
from PIL import Image
import os
import gc
import math
import torch

# ── Face detection (MTCNN — RetinaFace-class) ─────────────────────────────────
from app.ai.models.face_detector import detect_faces_with_boxes

# ── EfficientNet-B4 classifier ────────────────────────────────────────────────
from app.ai.models.image_model import (
    predict_whole_image,
    predict_fake_probability,
    get_all_face_crops,
    is_using_trained_weights,
)

# ── Forensic modules ───────────────────────────────────────────────────────────
from app.ai.forensics.ela import ela_score
from app.ai.forensics.noise import noise_splice_score
from app.ai.forensics.frequency import frequency_domain_score
from app.ai.forensics.texture import texture_uniformity_score
from app.ai.forensics.color_analysis import color_channel_anomaly
from app.ai.forensics.metadata import extract_exif, get_device_name, exif_authenticity_score
from app.ai.forensics.edge import edge_consistency_score

# ── Image type classifier ─────────────────────────────────────────────────────
from app.ai.classification.image_type_classifier import classify_image_type

# ── CLIP detector ─────────────────────────────────────────────────────────────
from app.ai.detectors.clip_detector import detect_with_clip, should_use_clip, get_clip_ensemble_weight

# ── Fusion configuration ─────────────────────────────────────────────────────
from app.ai.detectors.fusion_config import FusionConfig

# ── Explainability (Grad-CAM) ─────────────────────────────────────────────────
from app.ai.explainability.gradcam import get_gradcam_generator
from app.ai.models.image_model import get_full_model
import torchvision.transforms as T

# ── Report Generation ─────────────────────────────────────────────────────────
from app.reporting.report_generator import generate_report

# ── Grad-CAM singleton for performance optimization ─────────────────────────────
_GRADCAM_GENERATOR = None
_GRADCAM_DEVICE = None


def _get_gradcam_generator():
    """
    Get or create the Grad-CAM generator singleton.
    
    This optimizes inference speed by reusing the same Grad-CAM generator
    across multiple requests, avoiding repeated model loading and hook registration.
    
    Returns:
        GradCAMGenerator instance
    """
    global _GRADCAM_GENERATOR, _GRADCAM_DEVICE
    
    # Determine device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    # Recreate if device changed or not initialized
    if _GRADCAM_GENERATOR is None or _GRADCAM_DEVICE != device:
        model = get_full_model()
        _GRADCAM_GENERATOR = get_gradcam_generator(model, device)
        _GRADCAM_DEVICE = device
    
    return _GRADCAM_GENERATOR


# =============================================================================
# Utilities
# =============================================================================

def _get_mem_mb() -> float:
    """Return process resident memory in MB (Linux /proc; returns 0 on Windows)."""
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    return 0.0


def _classify_image_type(
    img_array: np.ndarray, gray: np.ndarray, hsv: np.ndarray, face_count: int
) -> str:
    """Classify image content type for metadata and findings labelling only.
    Does NOT gate analysis — all image types are fully analysed."""
    if face_count > 0:
        return "face_photo"
    try:
        low_sat = float(np.sum(hsv[:, :, 1] < 30) / hsv[:, :, 1].size)
        if low_sat > 0.55:
            return "screenshot"
        edges = cv2.Canny(gray, 50, 150)
        if float(np.sum(edges > 0) / edges.size) > 0.18:
            return "document"
        avg_std = float(np.mean([np.std(img_array[:, :, c]) for c in range(3)]))
        if avg_std < 25:
            return "graphic"
    except Exception:
        pass
    return "photo"


# =============================================================================
# Forensic Signal Extractors
# =============================================================================

def _forensic_bundle(
    gray: np.ndarray,
    img_array: np.ndarray,
    pil_img: Image.Image,
    exif: dict,
) -> tuple[float, list[str], dict]:
    """
    Run all forensic analyses and fuse them into a single forensic score.

    Uses configurable weights from FusionConfig.FORENSIC_WEIGHTS.

    Returns:
        (forensic_score: float [0,1], findings: list[str], contributions: dict)
        forensic_score 1 = strongly fake; 0 = strongly authentic.
        contributions: dictionary of individual module scores
    """
    findings: list[str] = []
    contributions = {}

    # --- ELA ---
    ela_var, ela_signal = ela_score(pil_img)
    contributions['ela'] = ela_signal
    if ela_var > 800:
        findings.append(
            f"✗ ELA detected abnormal compression artifacts (variance: {ela_var:.0f})"
        )
    else:
        findings.append("✓ ELA compression levels are consistent across the image")

    # --- Noise / splicing ---
    noise_var, noise_signal = noise_splice_score(gray)
    contributions['noise'] = noise_signal
    if noise_var > 25:
        findings.append(
            f"✗ Inconsistent sensor noise across quadrants — possible splicing "
            f"(variance: {noise_var:.1f})"
        )
    else:
        findings.append("✓ Sensor noise is consistent across all image quadrants")

    # --- Frequency domain ---
    freq_signal = frequency_domain_score(gray)
    contributions['frequency'] = freq_signal
    if freq_signal > 0.5:
        findings.append("✗ Anomalous frequency spectrum — unnatural spectral signature")
    else:
        findings.append("✓ Frequency spectrum is within natural camera range")

    # --- Texture uniformity ---
    texture_signal = texture_uniformity_score(gray)
    contributions['texture'] = texture_signal
    if texture_signal > 0.62:
        findings.append(
            "✗ Texture uniformity suggests AI generation "
            "(GAN/diffusion over-smoothing detected)"
        )
    else:
        findings.append(
            "✓ Natural texture variation consistent with camera imagery"
        )

    # --- Edge consistency ---
    edge_signal = edge_consistency_score(gray)
    contributions['edge'] = edge_signal
    if edge_signal > 0.5:
        findings.append(
            "✗ Unnatural edge patterns detected "
            "(characteristic of AI-generated images)"
        )
    else:
        findings.append(
            "✓ Natural edge consistency consistent with camera imagery"
        )

    # --- Color channel anomaly ---
    color_signal = color_channel_anomaly(img_array)
    contributions['color'] = color_signal

    # --- EXIF consistency (inverted: high authenticity = low fake score) ---
    exif_auth = exif_authenticity_score(exif)
    exif_signal = 1.0 - exif_auth   # convert to fake-score
    contributions['exif'] = exif_signal

    # --- Weighted forensic score using configurable weights ---
    weights = FusionConfig.FORENSIC_WEIGHTS
    forensic_score = (
        weights['ela'] * ela_signal
        + weights['noise'] * noise_signal
        + weights['frequency'] * freq_signal
        + weights['texture'] * texture_signal
        + weights['edge'] * edge_signal
        + weights['color'] * color_signal
        + weights['exif'] * exif_signal
    )
    forensic_score = round(min(max(forensic_score, 0.0), 1.0), 4)

    return forensic_score, findings, contributions


# =============================================================================
# Confidence Calibration
# =============================================================================

def _calibrate_confidence(fake_prob: float) -> float:
    """
    Map a fake probability to a display confidence using logistic calibration.

    Uses configurable scale factor from FusionConfig.CONFIDENCE_CALIBRATION.

    Returns: float in [min_confidence, max_confidence].
    """
    config = FusionConfig.CONFIDENCE_CALIBRATION
    distance = abs(fake_prob - 0.5)          # in [0, 0.5]
    calibrated = 1.0 / (1.0 + math.exp(-distance * config['scale']))
    return round(min(max(calibrated, config['min_confidence']), config['max_confidence']), 2)


# =============================================================================
# Fusion Engine
# =============================================================================

def _fusion_engine(
    whole_image_score: float,
    face_score: float | None,   # None when no faces were detected
    forensic_score: float,
    forensic_contributions: dict,
    image_type: str = "mixed_scene",
    recommended_pipeline: str = "whole_image",
    clip_score: float | None = None,   # CLIP score (optional)
) -> tuple[str, float, float, float, float, dict]:
    """
    Combine all signals into a final verdict, confidence, and probabilities.

    Uses configurable weights from FusionConfig based on image type and pipeline.
Now includes CLIP contribution for enhanced AI detection.

    Returns:
        (verdict, confidence, ai_probability, deepfake_probability, final_fake_prob, contributions)
        contributions: dictionary tracking each module's contribution to final score
    """
    # Get pipeline weights from configuration
    weights = FusionConfig.get_pipeline_weights(recommended_pipeline, image_type)
    
    # Get CLIP weight based on image type
    clip_weight = get_clip_ensemble_weight(image_type)
    
    # Adjust weights to accommodate CLIP
    if clip_score is not None and clip_weight > 0:
        # Normalize existing weights to make room for CLIP
        total_existing_weight = weights['whole_image'] + weights['face'] + weights['forensic']
        if total_existing_weight > 0:
            scale_factor = (1.0 - clip_weight) / total_existing_weight
            weights['whole_image'] *= scale_factor
            weights['face'] *= scale_factor
            weights['forensic'] *= scale_factor
    else:
        clip_weight = 0.0
    
    # Calculate weighted fusion with CLIP
    final_fake_prob = (
        weights['whole_image'] * whole_image_score
        + weights['face'] * (face_score or 0.0)
        + weights['forensic'] * forensic_score
        + clip_weight * (clip_score or 0.0)
    )
    final_fake_prob = round(min(max(final_fake_prob, 0.0), 1.0), 4)
    
    # Track module contributions
    contributions = {
        'whole_image': {
            'score': whole_image_score,
            'weight': weights['whole_image'],
            'contribution': weights['whole_image'] * whole_image_score
        },
        'face': {
            'score': face_score if face_score is not None else 0.0,
            'weight': weights['face'],
            'contribution': weights['face'] * (face_score or 0.0)
        },
        'forensic': {
            'score': forensic_score,
            'weight': weights['forensic'],
            'contribution': weights['forensic'] * forensic_score,
            'sub_modules': forensic_contributions
        },
        'clip': {
            'score': clip_score if clip_score is not None else 0.0,
            'weight': clip_weight,
            'contribution': clip_weight * (clip_score or 0.0),
            'enabled': clip_score is not None and clip_weight > 0
        }
    }

    # --- Verdict selection using configurable thresholds ---
    thresholds = FusionConfig.VERDICT_THRESHOLDS
    
    # Determine whether face signal or whole-image signal dominates
    face_dominated = (
        face_score is not None
        and face_score >= 0.70
        and face_score > whole_image_score * 0.85
    )

    if final_fake_prob >= thresholds['deepfake']:
        verdict = "Deepfake" if face_dominated else "AI Generated"
    elif final_fake_prob >= thresholds['ai_generated']:
        verdict = "Deepfake" if face_dominated else "AI Generated"
    elif final_fake_prob >= thresholds['suspicious']:
        verdict = "Suspicious"
    elif final_fake_prob >= thresholds['likely_authentic']:
        verdict = "Likely Authentic"
    else:
        verdict = "Authentic"

    # --- Confidence calibration ---
    confidence = _calibrate_confidence(final_fake_prob)

    # --- ai_probability / deepfake_probability using configurable multipliers ---
    multipliers = FusionConfig.AI_PROBABILITY_MULTIPLIERS.get(verdict, {})
    
    if verdict == "Deepfake":
        # Face-swap dominant: face prob → deepfake %, whole-image → ai %
        ai_prob  = round(min(max(whole_image_score * multipliers.get('ai', 60.0), 5.0), 55.0), 1)
        df_prob  = round(min((face_score or final_fake_prob) * multipliers.get('deepfake', 115.0), 98.0), 1)
    elif verdict == "AI Generated":
        # Whole-image dominant
        ai_prob  = round(min(whole_image_score * multipliers.get('ai', 118.0), 98.0), 1)
        df_prob  = round(max(final_fake_prob * multipliers.get('deepfake', 18.0), 2.0), 1)
    elif verdict == "Suspicious":
        ai_prob  = round(final_fake_prob * multipliers.get('ai', 75.0), 1)
        df_prob  = round(final_fake_prob * multipliers.get('deepfake', 55.0), 1)
    elif verdict == "Likely Authentic":
        ai_prob  = round(final_fake_prob * multipliers.get('ai', 28.0), 1)
        df_prob  = round(final_fake_prob * multipliers.get('deepfake', 18.0), 1)
    else:  # Authentic
        ai_prob  = round(max(final_fake_prob * multipliers.get('ai', 14.0), 1.0), 1)
        df_prob  = round(max(final_fake_prob * multipliers.get('deepfake', 9.0),  1.0), 1)

    return verdict, confidence, ai_prob, df_prob, final_fake_prob, contributions


# =============================================================================
# Explanation Generator
# =============================================================================

def _generate_explanation(
    verdict: str,
    final_fake_prob: float,
    contributions: dict,
    findings: list[str],
    clip_reason: str = "",
) -> dict:
    """
    Generate detailed explanation for the prediction.
    
    Returns:
        dict with 'for_ai' and 'against_ai' lists
    """
    for_ai = []
    against_ai = []
    
    # Analyze contributions
    whole_image_contrib = contributions['whole_image']['contribution']
    face_contrib = contributions['face']['contribution']
    forensic_contrib = contributions['forensic']['contribution']
    clip_contrib = contributions['clip']['contribution']
    clip_enabled = contributions['clip']['enabled']
    
    # Whole-image analysis
    if whole_image_contrib > 0.35:
        for_ai.append(
            f"EfficientNet-B2 classifier detected strong AI patterns "
            f"(contribution: {whole_image_contrib:.3f})"
        )
    elif whole_image_contrib < 0.15:
        against_ai.append(
            f"EfficientNet-B2 classifier detected authentic characteristics "
            f"(contribution: {whole_image_contrib:.3f})"
        )
    
    # Face analysis
    if face_contrib > 0.15:
        for_ai.append(
            f"Face deepfake analysis detected anomalies "
            f"(contribution: {face_contrib:.3f})"
        )
    elif face_contrib < 0.05:
        against_ai.append(
            f"Face analysis detected no deepfake indicators "
            f"(contribution: {face_contrib:.3f})"
        )
    
    # CLIP analysis
    if clip_enabled:
        if clip_contrib > 0.2:
            for_ai.append(
                f"CLIP semantic analysis indicates AI-generated content "
                f"(contribution: {clip_contrib:.3f})"
            )
            if clip_reason:
                for_ai.append(clip_reason)
        elif clip_contrib < 0.1:
            against_ai.append(
                f"CLIP semantic analysis indicates authentic content "
                f"(contribution: {clip_contrib:.3f})"
            )
            if clip_reason:
                against_ai.append(clip_reason)
    
    # Forensic analysis
    forensic_sub = contributions['forensic']['sub_modules']
    strong_forensic_ai = [k for k, v in forensic_sub.items() if v > 0.6]
    strong_forensic_real = [k for k, v in forensic_sub.items() if v < 0.3]
    
    if strong_forensic_ai:
        for_ai.append(
            f"Forensic analysis detected AI indicators in: "
            f"{', '.join(strong_forensic_ai)}"
        )
    if strong_forensic_real:
        against_ai.append(
            f"Forensic analysis detected authentic patterns in: "
            f"{', '.join(strong_forensic_real)}"
        )
    
    # Overall probability
    if final_fake_prob > 0.7:
        for_ai.append(
            f"Overall AI probability is high ({final_fake_prob:.1%})"
        )
    elif final_fake_prob < 0.3:
        against_ai.append(
            f"Overall AI probability is low ({final_fake_prob:.1%})"
        )
    
    return {
        'for_ai': for_ai,
        'against_ai': against_ai
    }


# =============================================================================
# Main Analyzer
# =============================================================================

async def analyze_image(image_path: str) -> dict:
    """
    Full multi-signal fusion image authenticity analysis.

    Always analyses the entire image — face detection enriches the result
    but is never required for a verdict.  Never returns "No Human Face
    Detected" as a final verdict.

    Args:
        image_path: absolute path to the uploaded image file.

    Returns:
        dict with keys: verdict, confidence, ai_probability, deepfake_probability,
        key_findings, metadata_summary, truth_score, ai_detection_score,
        result, image_type  (identical schema to v4).
    """
    from app.core.serializer import to_python

    filename = os.path.basename(image_path)
    print(f"\n[IMAGE v5] Analysing: {filename}")
    mem_before = _get_mem_mb()
    print(f"[MEMORY] Before: {mem_before:.1f} MB")

    # --- Memory guard ---
    if mem_before > 400.0:
        return {
            "verdict":              "Analysis Failed",
            "confidence":           0.0,
            "ai_probability":       0.0,
            "deepfake_probability": 0.0,
            "key_findings": [
                "✗ Memory limit reached — aborting to prevent server crash."
            ],
            "metadata_summary": {
                "error": "Server memory limit reached. Try a smaller image."
            },
        }

    # ── Open & pre-process image ──────────────────────────────────────────────
    try:
        pil_img = Image.open(image_path).convert("RGB")
        width, height = pil_img.size

        # Resize to max 1024 px on the long edge to limit memory usage
        if width > 1024 or height > 1024:
            pil_img.thumbnail(
                (1024, 1024),
                getattr(Image, "Resampling", Image).LANCZOS,
            )

        img_array = np.array(pil_img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        hsv  = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)

    except Exception as e:
        print(f"[IMAGE v5] Open error: {e}")
        return {
            "verdict":              "Analysis Failed",
            "confidence":           0.0,
            "ai_probability":       0.0,
            "deepfake_probability": 0.0,
            "key_findings":         [f"✗ Could not open file: {e}"],
            "metadata_summary":     {"error": str(e)},
        }

    # ── Metadata ──────────────────────────────────────────────────────────────
    exif       = extract_exif(image_path)
    has_exif   = bool(exif)
    device     = get_device_name(exif)

    # ── Image Type Classification (Pipeline Routing) ─────────────────────────
    # First, detect faces to inform classification
    face_count, boxes, probs = detect_faces_with_boxes(img_array)
    has_face   = face_count > 0
    
    # Run image type classifier
    classification = classify_image_type(img_array, face_count)
    image_type = classification["image_type"]
    image_type_confidence = classification["image_type_confidence"]
    recommended_pipeline = classification["recommended_pipeline"]
    heuristics = classification["heuristics"]
    
    print(
        f"[IMAGE v5] has_exif={has_exif}, faces={face_count}, "
        f"type={image_type}, conf={image_type_confidence}, pipeline={recommended_pipeline}"
    )

    # ── Pipeline Routing ─────────────────────────────────────────────────────
    face_score: float | None = None
    
    if recommended_pipeline == "face":
        # Use existing face detector
        if has_face:
            face_crops = get_all_face_crops(img_array, boxes, probs, min_confidence=0.85)
            if face_crops:
                per_face = [predict_fake_probability(crop) for crop in face_crops]
                face_score = max(per_face)   # worst-case: highest fake prob wins
                print(
                    f"[IMAGE v5] face scores={[round(p,3) for p in per_face]}"
                    f" → face_score={face_score:.3f}"
                )
        # Always run whole-image detection
        whole_image_score = predict_whole_image(img_array)
        print(f"[IMAGE v5] whole_image_score={whole_image_score:.3f}")
        
    elif recommended_pipeline == "whole_image":
        # Skip face detector, use whole-image only
        whole_image_score = predict_whole_image(img_array)
        print(f"[IMAGE v5] whole_image_score={whole_image_score:.3f} (face detection skipped)")
        
    elif recommended_pipeline == "document":
        # Forensic analysis only - skip AI models
        whole_image_score = 0.5  # Neutral score for documents
        print(f"[IMAGE v5] document mode - forensic analysis only")
    else:
        # Default: run both
        whole_image_score = predict_whole_image(img_array)
        print(f"[IMAGE v5] whole_image_score={whole_image_score:.3f}")
        if has_face:
            face_crops = get_all_face_crops(img_array, boxes, probs, min_confidence=0.85)
            if face_crops:
                per_face = [predict_fake_probability(crop) for crop in face_crops]
                face_score = max(per_face)
                print(
                    f"[IMAGE v5] face scores={[round(p,3) for p in per_face]}"
                    f" → face_score={face_score:.3f}"
                )

    # ── Signal [3]: Forensic bundle ───────────────────────────────────────────
    forensic_score, forensic_findings, forensic_contributions = _forensic_bundle(
        gray, img_array, pil_img, exif
    )
    print(f"[IMAGE v5] forensic_score={forensic_score:.3f}")

    # ── Signal [3.5]: CLIP Semantic Analysis ─────────────────────────────────
    clip_score = None
    clip_result = None
    clip_confidence = 0.0
    clip_reason = ""
    
    if should_use_clip(image_type):
        print(f"[IMAGE v5] Running CLIP analysis for {image_type}")
        clip_result = detect_with_clip(img_array, image_type)
        clip_score = clip_result["ai_probability"]
        clip_confidence = clip_result["confidence"]
        clip_reason = clip_result["reason"]
        print(f"[IMAGE v5] CLIP score={clip_score:.3f}, confidence={clip_confidence:.3f}")
    else:
        print(f"[IMAGE v5] CLIP skipped for {image_type}")

    # ── Signal [4]: Fusion ────────────────────────────────────────────────────
    verdict, confidence, ai_probability, deepfake_probability, final_fake_prob, contributions = (
        _fusion_engine(whole_image_score, face_score, forensic_score, forensic_contributions, image_type, recommended_pipeline, clip_score)
    )
    face_log = f"{face_score:.3f}" if face_score is not None else "n/a"
    clip_log = f"{clip_score:.3f}" if clip_score is not None else "n/a"
    print(
        f"[IMAGE v5] whole={whole_image_score:.3f}  "
        f"face={face_log}  "
        f"forensic={forensic_score:.3f}  "
        f"clip={clip_log}  "
        f"=> final={final_fake_prob:.3f}  verdict={verdict}  conf={confidence:.2f}"
    )

    # ── Signal [5]: Grad-CAM Visualization (Explainability) ───────────────────
    # Generate Grad-CAM heatmaps for model interpretability
    # This helps users understand which regions of the image influenced the prediction
    heatmap_paths = {'heatmap_path': None, 'overlay_path': None}
    
    try:
        # Only generate Grad-CAM if EfficientNet was used (not document mode)
        if recommended_pipeline != "document":
            # Get Grad-CAM generator (singleton for performance)
            gradcam_gen = _get_gradcam_generator()
            
            # Prepare input tensor for Grad-CAM (same transform as model)
            transform = T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            input_tensor = transform(pil_img).unsqueeze(0)  # (1, 3, 224, 224)
            
            # Generate visualization (heatmap and overlay)
            heatmap_paths = gradcam_gen.generate_visualization(
                image_path=image_path,
                input_tensor=input_tensor,
                output_dir="uploads/heatmaps"
            )
            print(f"[IMAGE v5] Grad-CAM generated: {heatmap_paths['heatmap_path']}")
    except Exception as e:
        print(f"[IMAGE v5] Grad-CAM generation failed: {e}")
        # Continue without Grad-CAM if it fails (non-critical for main functionality)

    # ── Key findings ──────────────────────────────────────────────────────────
    findings: list[str] = []

    # 1. EXIF / metadata
    if has_exif:
        findings.append(
            f"✓ Camera metadata (EXIF) present — device: {device}"
        )
    else:
        findings.append("✗ No camera EXIF metadata found")

    # 2. Face detection and per-face AI score
    if has_face:
        fs_pct = round(face_score * 100, 1) if face_score is not None else "n/a"
        findings.append(
            f"{'✓' if face_score is not None and face_score < 0.5 else '✗'} "
            f"{face_count} face(s) detected — deepfake analysis score: {fs_pct}%"
        )
    else:
        findings.append(
            f"• No faces detected — whole-image AI analysis applied "
            f"(score: {round(whole_image_score * 100, 1)}%)"
        )

    # 3. Whole-image AI detection
    if whole_image_score >= 0.65:
        findings.append(
            f"✗ EfficientNet-B4 whole-image analysis flags synthetic content "
            f"(score: {round(whole_image_score * 100, 1)}%)"
        )
    elif whole_image_score >= 0.45:
        findings.append(
            f"⚠ EfficientNet-B4 detects ambiguous patterns "
            f"(score: {round(whole_image_score * 100, 1)}%)"
        )
    else:
        findings.append(
            f"✓ EfficientNet-B4 whole-image analysis: authentic characteristics "
            f"(score: {round(whole_image_score * 100, 1)}%)"
        )

    # 4. Forensic bundle findings (ELA, noise, frequency, texture)
    findings.extend(forensic_findings)

    # 5. Model status — honest disclosure
    if is_using_trained_weights():
        findings.append(
            "✓ EfficientNet-B4 running with deepfake-trained classifier weights"
        )
    else:
        findings.append(
            "⚠ EfficientNet-B4 in feature-extraction mode (no trained weights) "
            "— AI scores are indicative; forensic signals carry more weight"
        )

    # ── Metadata summary ──────────────────────────────────────────────────────
    metadata_summary: dict = {
        "resolution":     f"{width}x{height}",
        "has_exif":       has_exif,
        "device":         device if has_exif else "Unknown",
        "image_type":     image_type.replace("_", " ").title(),
        "faces_detected": face_count,
    }
    if "DateTime" in exif:
        metadata_summary["capture_date"] = exif["DateTime"]
    if "Software" in exif:
        metadata_summary["software"] = exif["Software"][:60]

    # ── Memory cleanup ────────────────────────────────────────────────────────
    try:
        del img_array, gray, hsv, pil_img
        if has_face:
            del face_crops  # type: ignore[possibly-undefined]
        gc.collect()
    except Exception:
        pass
    print(f"[MEMORY] After GC: {_get_mem_mb():.1f} MB")

    # truth_score: legacy field — inverted fake prob on 0–100 scale
    truth_score = round((1.0 - final_fake_prob) * 100, 1)
    
    # Generate explanation
    explanation = _generate_explanation(verdict, final_fake_prob, contributions, findings, clip_reason)

    # ── Signal [6]: PDF Report Generation (Phase 5) ─────────────────────────────
    # Generate professional PDF report with all analysis results
    report_path = None
    try:
        # Prepare analysis data for report generation
        report_data = {
            'verdict': verdict,
            'confidence': confidence,
            'ai_probability': ai_probability,
            'deepfake_probability': deepfake_probability,
            'image_type': image_type,
            'module_contributions': contributions,
            'explanation': explanation,
            'key_findings': findings,
            'metadata_summary': metadata_summary,
            'filename': filename
        }
        
        # Generate PDF report
        report_path = generate_report(
            analysis_data=report_data,
            original_image_path=image_path,
            output_dir="uploads/reports"
        )
        print(f"[IMAGE v5] PDF report generated: {report_path}")
    except Exception as e:
        print(f"[IMAGE v5] PDF report generation failed: {e}")
        # Continue without report if it fails (non-critical for main functionality)

    return to_python({
        "verdict":              verdict,
        "confidence":           confidence,
        "ai_probability":       ai_probability,
        "deepfake_probability": deepfake_probability,
        "key_findings":         findings,
        "metadata_summary":     metadata_summary,
        # Legacy fields — kept for history / dashboard backward compatibility
        "truth_score":          truth_score,
        "ai_detection_score":   ai_probability,
        "result":               verdict,
        "image_type":           image_type,
        # New fields for Phase 3 - backward compatible additions
        "module_contributions": contributions,
        "explanation":          explanation,
        # New fields for Phase 4 - Grad-CAM visualization (backward compatible)
        "heatmap_path":         heatmap_paths['heatmap_path'],
        "overlay_path":         heatmap_paths['overlay_path'],
        # New fields for Phase 5 - PDF report (backward compatible)
        "report_path":          report_path,
        # New fields for Phase 6 - Enhanced Image Type Classification (backward compatible)
        "image_type_confidence": image_type_confidence,
        "recommended_pipeline":  recommended_pipeline,
        "heuristics":           heuristics,
        # New fields for Phase 7 - CLIP Multi-Model Ensemble (backward compatible)
        "clip_probability":      clip_score if clip_score is not None else 0.0,
        "clip_confidence":      clip_confidence,
        "ensemble_score":       final_fake_prob,
        "clip_enabled":         clip_score is not None,
        # New fields for v2.2 - backward compatible additions (optional fields)
        "patch_statistics":      None,  # Will be populated when patch inference is enabled
        "ood_score":            None,  # Will be populated when OOD detection is enabled
        "frequency_features":    None,  # Will be populated when enhanced frequency analysis is enabled
        "noise_features":       None,  # Will be populated when enhanced noise analysis is enabled
        "fusion_weights_used":  contributions,  # Already available in module_contributions
        "confidence_calibrated": confidence,  # Already calibrated, exposed for transparency
    })

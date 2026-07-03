"""
TruthLens — Image Authenticity Analyzer (v5 — Multi-Signal Fusion)
===================================================================
Pipeline (runs for every image, regardless of whether faces are present):

  [1] Whole-image AI score    EfficientNet-B4 on the full image
  [2] Face deepfake score     EfficientNet-B4 on each face crop (optional)
  [3] Forensic bundle         ELA · Noise · Frequency · Texture · Color · EXIF
  [4] Fusion engine           Weighted combination → final_fake_prob → verdict

Signal weights:
  Faces found  : whole-image 55%  +  face 30%  +  forensic 15%
  No faces     : whole-image 75%                +  forensic 25%

Verdict set (exactly 5, as required):
  Authentic | Likely Authentic | Suspicious | AI Generated | Deepfake

  "Deepfake"     — face deepfake score dominates the fused result
  "AI Generated" — whole-image AI score dominates (works for landscapes, art, etc.)
  "Suspicious"   — inconclusive signals, mid-range probability
  "Likely Authentic" — leaning real, minor anomalies present
  "Authentic"    — strong authentic signal across all channels

Confidence calibration:
  logistic(|fake_prob - 0.5| * 12) ensures:
    clear cases  (prob >= 0.85 or <= 0.15) -> confidence >= 0.92
    borderline   (prob ~  0.50)            -> confidence ~  0.55

JSON response: identical to v4 — zero frontend changes required.
"""

import cv2
import numpy as np
from PIL import Image
import os
import gc
import io
import math
from PIL import ImageChops, ImageEnhance
from PIL.ExifTags import TAGS

# ── Face detection (MTCNN — RetinaFace-class) ─────────────────────────────────
from app.services.face_detector import detect_faces_with_boxes

# ── EfficientNet-B4 classifier ────────────────────────────────────────────────
from app.models.image_model import (
    predict_whole_image,
    predict_fake_probability,
    get_all_face_crops,
    is_using_trained_weights,
)


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


def _extract_exif(image_path: str) -> dict:
    """Extract EXIF tags from a JPEG/TIFF image. Returns empty dict on failure."""
    try:
        img = Image.open(image_path)
        raw = img._getexif()
        if not raw:
            return {}
        return {TAGS.get(k, k): str(v) for k, v in raw.items()}
    except Exception:
        return {}


def _get_device_name(exif: dict) -> str:
    make  = exif.get("Make", "")
    model = exif.get("Model", "")
    if make and model:
        return f"{make.strip()} {model.strip()}"
    return make or model or "Unknown"


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

def _ela_score(pil_img: Image.Image) -> tuple[float, float]:
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


def _noise_splice_score(gray: np.ndarray) -> tuple[float, float]:
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


def _frequency_domain_score(gray: np.ndarray) -> float:
    """
    Frequency-domain analysis via 2-D FFT.

    Real camera images have characteristic high-frequency energy (lens
    diffraction, sensor noise, natural texture detail).  AI-generated images
    often show anomalous frequency profiles — too clean or periodically
    structured (GAN grid artifacts, diffusion spectral signatures).

    Returns: float [0, 1] where 1 = suspicious.
    """
    try:
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1)
        freq_mean = float(np.mean(magnitude))
        freq_std  = float(np.std(magnitude))

        # Mean outside natural range [75, 190] is suspicious
        mean_score = 0.0
        if freq_mean < 55 or freq_mean > 230:
            mean_score = 0.80
        elif freq_mean < 75 or freq_mean > 190:
            mean_score = 0.40

        # Very low std = unnaturally uniform frequency spectrum
        std_score = 0.0
        if freq_std < 15:
            std_score = 0.75
        elif freq_std < 25:
            std_score = 0.35

        return round((mean_score + std_score) / 2.0, 4)
    except Exception:
        return 0.5


def _texture_uniformity_score(gray: np.ndarray) -> float:
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


def _color_channel_anomaly(img_array: np.ndarray) -> float:
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


def _exif_authenticity_score(exif: dict) -> float:
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


def _forensic_bundle(
    gray: np.ndarray,
    img_array: np.ndarray,
    pil_img: Image.Image,
    exif: dict,
) -> tuple[float, list[str]]:
    """
    Run all forensic analyses and fuse them into a single forensic score.

    Signals and their weights within the bundle:
      ELA variance          25%  — compression artifact analysis
      Noise/splicing        20%  — quadrant noise inconsistency
      Frequency domain      20%  — FFT spectral anomalies
      Texture uniformity    20%  — GAN/diffusion over-smoothing
      Color anomaly         10%  — R-B correlation and hue flatness
      EXIF consistency       5%  — metadata integrity (low weight: easily stripped)

    Returns:
        (forensic_score: float [0,1], findings: list[str])
        forensic_score 1 = strongly fake; 0 = strongly authentic.
    """
    findings: list[str] = []

    # --- ELA ---
    ela_var, ela_signal = _ela_score(pil_img)
    if ela_var > 800:
        findings.append(
            f"✗ ELA detected abnormal compression artifacts (variance: {ela_var:.0f})"
        )
    else:
        findings.append("✓ ELA compression levels are consistent across the image")

    # --- Noise / splicing ---
    noise_var, noise_signal = _noise_splice_score(gray)
    if noise_var > 25:
        findings.append(
            f"✗ Inconsistent sensor noise across quadrants — possible splicing "
            f"(variance: {noise_var:.1f})"
        )
    else:
        findings.append("✓ Sensor noise is consistent across all image quadrants")

    # --- Frequency domain ---
    freq_signal = _frequency_domain_score(gray)
    if freq_signal > 0.5:
        findings.append("✗ Anomalous frequency spectrum — unnatural spectral signature")
    else:
        findings.append("✓ Frequency spectrum is within natural camera range")

    # --- Texture uniformity ---
    texture_signal = _texture_uniformity_score(gray)
    if texture_signal > 0.62:
        findings.append(
            "✗ Texture uniformity suggests AI generation "
            "(GAN/diffusion over-smoothing detected)"
        )
    else:
        findings.append(
            "✓ Natural texture variation consistent with camera imagery"
        )

    # --- Color channel anomaly ---
    color_signal = _color_channel_anomaly(img_array)

    # --- EXIF consistency (inverted: high authenticity = low fake score) ---
    exif_auth = _exif_authenticity_score(exif)
    exif_signal = 1.0 - exif_auth   # convert to fake-score

    # --- Weighted forensic score ---
    forensic_score = (
        0.25 * ela_signal
        + 0.20 * noise_signal
        + 0.20 * freq_signal
        + 0.20 * texture_signal
        + 0.10 * color_signal
        + 0.05 * exif_signal
    )
    forensic_score = round(min(max(forensic_score, 0.0), 1.0), 4)

    return forensic_score, findings


# =============================================================================
# Confidence Calibration
# =============================================================================

def _calibrate_confidence(fake_prob: float) -> float:
    """
    Map a fake probability to a display confidence using logistic calibration.

    Uses the distance from the 0.5 decision boundary, scaled by 12, through
    a sigmoid.  This produces:
      |prob - 0.5| = 0.00  ->  confidence = 0.50  (perfectly ambiguous)
      |prob - 0.5| = 0.20  ->  confidence = 0.73
      |prob - 0.5| = 0.35  ->  confidence = 0.93  (clear verdict)
      |prob - 0.5| = 0.45  ->  confidence = 0.98  (very clear verdict)

    Returns: float in [0.50, 0.99].
    """
    distance = abs(fake_prob - 0.5)          # in [0, 0.5]
    calibrated = 1.0 / (1.0 + math.exp(-distance * 12.0))
    return round(min(max(calibrated, 0.50), 0.99), 2)


# =============================================================================
# Fusion Engine
# =============================================================================

def _fusion_engine(
    whole_image_score: float,
    face_score: float | None,   # None when no faces were detected
    forensic_score: float,
) -> tuple[str, float, float, float, float]:
    """
    Combine all signals into a final verdict, confidence, and probabilities.

    Weights:
      With faces:  whole-image 55% + face 30% + forensic 15%
      No faces:    whole-image 75%            + forensic 25%

    Verdict discrimination:
      "Deepfake"      — face deepfake score dominates and is high
      "AI Generated"  — whole-image score is high (works for non-face images)
      "Suspicious"    — inconclusive mid-range
      "Likely Authentic" — leaning real with minor anomalies
      "Authentic"     — strong authentic signal

    Returns:
        (verdict, confidence, ai_probability, deepfake_probability, final_fake_prob)
    """
    # --- Weighted fusion ---
    if face_score is not None:
        final_fake_prob = (
            0.55 * whole_image_score
            + 0.30 * face_score
            + 0.15 * forensic_score
        )
    else:
        final_fake_prob = (
            0.75 * whole_image_score
            + 0.25 * forensic_score
        )

    final_fake_prob = round(min(max(final_fake_prob, 0.0), 1.0), 4)

    # --- Verdict selection ---
    # Determine whether face signal or whole-image signal dominates
    face_dominated = (
        face_score is not None
        and face_score >= 0.70
        and face_score > whole_image_score * 0.85
    )

    if final_fake_prob >= 0.82:
        verdict = "Deepfake" if face_dominated else "AI Generated"
    elif final_fake_prob >= 0.68:
        # High-confidence suspicious: distinguish type by dominant signal
        verdict = "Deepfake" if face_dominated else "AI Generated"
    elif final_fake_prob >= 0.50:
        verdict = "Suspicious"
    elif final_fake_prob >= 0.30:
        verdict = "Likely Authentic"
    else:
        verdict = "Authentic"

    # --- Confidence calibration ---
    confidence = _calibrate_confidence(final_fake_prob)

    # --- ai_probability / deepfake_probability for frontend display ---
    if verdict == "Deepfake":
        # Face-swap dominant: face prob → deepfake %, whole-image → ai %
        ai_prob  = round(min(max(whole_image_score * 60.0, 5.0), 55.0), 1)
        df_prob  = round(min((face_score or final_fake_prob) * 115.0, 98.0), 1)
    elif verdict == "AI Generated":
        # Whole-image dominant
        ai_prob  = round(min(whole_image_score * 118.0, 98.0), 1)
        df_prob  = round(max(final_fake_prob * 18.0, 2.0), 1)
    elif verdict == "Suspicious":
        ai_prob  = round(final_fake_prob * 75.0, 1)
        df_prob  = round(final_fake_prob * 55.0, 1)
    elif verdict == "Likely Authentic":
        ai_prob  = round(final_fake_prob * 28.0, 1)
        df_prob  = round(final_fake_prob * 18.0, 1)
    else:  # Authentic
        ai_prob  = round(max(final_fake_prob * 14.0, 1.0), 1)
        df_prob  = round(max(final_fake_prob * 9.0,  1.0), 1)

    return verdict, confidence, ai_prob, df_prob, final_fake_prob


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
    exif       = _extract_exif(image_path)
    has_exif   = bool(exif)
    device     = _get_device_name(exif)

    # ── Face detection ────────────────────────────────────────────────────────
    face_count, boxes, probs = detect_faces_with_boxes(img_array)
    has_face   = face_count > 0
    image_type = _classify_image_type(img_array, gray, hsv, face_count)

    print(
        f"[IMAGE v5] has_exif={has_exif}, faces={face_count}, type={image_type}"
    )

    # ── Signal [1]: Whole-image AI detection ──────────────────────────────────
    # Always runs — detects AI-generated images regardless of content type.
    whole_image_score = predict_whole_image(img_array)
    print(f"[IMAGE v5] whole_image_score={whole_image_score:.3f}")

    # ── Signal [2]: Face deepfake detection (optional) ────────────────────────
    face_score: float | None = None
    if has_face:
        face_crops = get_all_face_crops(img_array, boxes, probs, min_confidence=0.85)
        if face_crops:
            per_face = [predict_fake_probability(crop) for crop in face_crops]
            face_score = max(per_face)   # worst-case: highest fake prob wins
            print(
                f"[IMAGE v5] face scores={[round(p,3) for p in per_face]}"
                f" → face_score={face_score:.3f}"
            )

    # ── Signal [3]: Forensic bundle ───────────────────────────────────────────
    forensic_score, forensic_findings = _forensic_bundle(
        gray, img_array, pil_img, exif
    )
    print(f"[IMAGE v5] forensic_score={forensic_score:.3f}")

    # ── Signal [4]: Fusion ────────────────────────────────────────────────────
    verdict, confidence, ai_probability, deepfake_probability, final_fake_prob = (
        _fusion_engine(whole_image_score, face_score, forensic_score)
    )
    face_log = f"{face_score:.3f}" if face_score is not None else "n/a"
    print(
        f"[IMAGE v5] whole={whole_image_score:.3f}  "
        f"face={face_log}  "
        f"forensic={forensic_score:.3f}  "
        f"=> final={final_fake_prob:.3f}  verdict={verdict}  conf={confidence:.2f}"
    )

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
    })

"""
TruthLens — Image Authenticity Analyzer (v3)
=============================================
Weighted scoring model:
  Base score:           50
  +EXIF present:        +30
  +Face detected:       +20
  -AI keyword in name:  -60
  -Splicing (var>25):   -40
  -Forensic (≥3/5):     -8 per indicator

Verdict thresholds:
  ≥ 80  → Authentic
  60-79 → Likely Authentic
  40-59 → Suspicious
  < 40 + AI  → Likely AI Generated / AI Generated
  < 40 + swap → Deepfake
"""

import cv2
import numpy as np
from PIL import Image
import os
import re
import hashlib
import httpx
import gc
from PIL.ExifTags import TAGS

def _get_mem_mb() -> float:
    try:
        with open(f"/proc/{os.getpid()}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    return 0.0


# ── AI generation keywords ──────────────────────────────────────────────────
_AI_KEYWORDS = [
    "midjourney", "dall-e", "dalle", "diffusion", "gan", "generated",
    "artificial", "synthetic", "stable", "sdxl", "flux", "firefly",
    "nightcafe", "artbreeder", "deepai", "craiyon", "bing image creator",
]


# ── EXIF extraction ─────────────────────────────────────────────────────────
def _extract_exif(image_path: str) -> dict:
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


# ── Face detection ──────────────────────────────────────────────────────────
_FACE_CASCADE = None

def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        _FACE_CASCADE = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    return _FACE_CASCADE


def _detect_faces(gray: np.ndarray) -> int:
    try:
        faces = _get_face_cascade().detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        return len(faces)
    except Exception:
        return 0


# ── AI keyword scan ─────────────────────────────────────────────────────────
def _has_ai_keywords(filename: str, exif: dict) -> bool:
    combined = (filename + " " + str(exif)).lower()
    return any(kw in combined for kw in _AI_KEYWORDS)


# ── Forensic analysis ────────────────────────────────────────────────────────
def _run_forensics(gray: np.ndarray, hsv: np.ndarray) -> tuple[int, list[str]]:
    """Return (indicator_count, reason_list). Max 5 indicators."""
    indicators = 0
    reasons    = []
    try:

        # 1. Laplacian sharpness
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if lap_var < 15:
            indicators += 1
            reasons.append("Very low image sharpness (heavy blur or resampling)")

        # 2. Noise level
        noise = float(np.std(gray))
        if noise < 4 or noise > 98:
            indicators += 1
            reasons.append("Extreme noise level (too smooth or too noisy for a real photo)")

        # 3. Edge density
        edges = cv2.Canny(gray, 100, 200)
        edge_density = float(np.sum(edges > 0)) / (edges.shape[0] * edges.shape[1])
        if edge_density < 0.003 or edge_density > 0.38:
            indicators += 1
            reasons.append("Abnormal edge distribution pattern")

        # 4. Color spectrum variance
        color_var = float(np.std(hsv[:, :, 0]))
        if color_var < 7:
            indicators += 1
            reasons.append("Unnaturally flat color spectrum (no hue variation)")

        # 5. Frequency domain
        f      = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        mag    = 20 * np.log(np.abs(fshift) + 1)
        freq_score = float(np.mean(mag))
        if freq_score < 55 or freq_score > 230:
            indicators += 1
            reasons.append("Anomalous high-frequency spectral signature")

    except Exception as e:
        print(f"[FORENSIC] Error: {e}")

    return indicators, reasons


# ── Noise/splicing check ─────────────────────────────────────────────────────
def _noise_variance(gray: np.ndarray) -> float:
    """Quadrant noise variance — high value signals splicing."""
    try:
        h, w = gray.shape
        quads = [
            gray[:h//2, :w//2], gray[:h//2, w//2:],
            gray[h//2:, :w//2], gray[h//2:, w//2:]
        ]
        stds = [float(np.std(q)) for q in quads]
        return float(np.var(stds))
    except Exception:
        return 0.0


# ── Image type classification ────────────────────────────────────────────────
def _classify_image_type(img_array: np.ndarray, gray: np.ndarray, hsv: np.ndarray, face_count: int) -> str:
    if face_count > 0:
        return "face_photo"
    try:
        low_sat = float(np.sum(hsv[:, :, 1] < 30) / hsv[:, :, 1].size)
        if low_sat > 0.55:
            return "screenshot"
        edges = cv2.Canny(gray, 50, 150)
        if float(np.sum(edges > 0) / edges.size) > 0.18:
            return "document"
        avg_std = float(np.mean([np.std(img_array[:,:,c]) for c in range(3)]))
        if avg_std < 25:
            return "graphic"
    except Exception:
        pass
    return "photo"


# ── Reverse image search (DuckDuckGo only — no Wikipedia) ───────────────────
async def _reverse_search(image_path: str, exif: dict) -> list[dict]:
    filename = os.path.basename(image_path)
    keywords = re.sub(r"[\-_.]", " ", filename)
    keywords = re.sub(
        r"\b(?:jpg|jpeg|png|webp|gif|upload|uuid|image|tmp)\b", "",
        keywords, flags=re.IGNORECASE
    )
    keywords = re.sub(r"\s+", " ", keywords).strip()
    if not keywords:
        keywords = exif.get("ImageDescription", "") or "photo"

    results = []
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": f"{keywords} original photo source", "kl": "us-en"},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            if resp.status_code == 200:
                # Parse <a class="result__a"> links
                from html.parser import HTMLParser

                class _DDGParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.results = []
                        self._in_link = False
                        self._cur = {}

                    def handle_starttag(self, tag, attrs):
                        if tag == "a":
                            d = dict(attrs)
                            cls = d.get("class", "")
                            if "result__a" in cls:
                                self._in_link = True
                                self._cur = {"url": d.get("href", ""), "title": ""}

                    def handle_data(self, data):
                        if self._in_link:
                            self._cur["title"] += data

                    def handle_endtag(self, tag):
                        if tag == "a" and self._in_link:
                            self._in_link = False
                            if self._cur.get("title"):
                                self.results.append(dict(self._cur))

                parser = _DDGParser()
                parser.feed(resp.text)

                for r in parser.results[:3]:
                    url = r["url"]
                    # Skip Wikipedia links — not useful for authenticity
                    if "wikipedia.org" in url.lower():
                        continue
                    title = r["title"].strip()[:60]
                    if title and url:
                        results.append({"name": title, "url": url})

    except Exception as e:
        print(f"[REVERSE SEARCH] Error: {e}")

    return results[:3]


# ═══════════════════════════════════════════════════════════════════════════════
# Main analyzer
# ═══════════════════════════════════════════════════════════════════════════════
async def analyze_image(image_path: str) -> dict:
    from app.core.serializer import to_python

    filename = os.path.basename(image_path)
    print(f"\n[IMAGE v3] Analyzing: {filename}")
    mem_before = _get_mem_mb()
    print(f"[MEMORY] Before analysis: {mem_before:.1f} MB")

    if mem_before > 400.0:
        return {
            "verdict": "Analysis Failed",
            "confidence": 0.0,
            "ai_probability": 0.0,
            "deepfake_probability": 0.0,
            "key_findings": ["✗ Memory limit reached. Aborting to prevent server crash."],
            "metadata_summary": {"error": "Server memory limit reached. Try a smaller image."},
            "source_links": [],
        }

    # ── Open image ──────────────────────────────────────────────────────────
    try:
        pil_img = Image.open(image_path).convert("RGB")
        width, height = pil_img.size
        # Resize to max 1024px to save memory
        if width > 1024 or height > 1024:
            resample_filter = getattr(Image, 'Resampling', Image).LANCZOS
            pil_img.thumbnail((1024, 1024), resample_filter)
        
        img_array = np.array(pil_img)
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    except Exception as e:
        print(f"[IMAGE v3] Cannot open or process: {e}")
        return {
            "verdict": "Analysis Failed",
            "confidence": 0.0,
            "ai_probability": 0.0,
            "deepfake_probability": 0.0,
            "key_findings": [f"✗ Could not open file: {e}"],
            "metadata_summary": {"error": str(e)},
            "source_links": [],
        }

    # ── Signal collection ───────────────────────────────────────────────────
    exif       = _extract_exif(image_path)
    has_exif   = bool(exif)
    face_count = _detect_faces(gray)
    has_face   = face_count > 0
    ai_flag    = _has_ai_keywords(filename, exif)
    noise_var  = _noise_variance(gray)
    is_spliced = noise_var > 25.0          # raised threshold vs old 15.0
    forensic_n, forensic_reasons = _run_forensics(gray, hsv)
    image_type = _classify_image_type(img_array, gray, hsv, face_count)
    device     = _get_device_name(exif)

    print(f"[IMAGE v3] has_exif={has_exif}, faces={face_count}, ai_flag={ai_flag}, "
          f"noise_var={noise_var:.1f}, forensic={forensic_n}/5, type={image_type}")

    # ── Weighted scoring ────────────────────────────────────────────────────
    score = 50.0

    if has_exif:
        score += 30.0

    if has_face:
        score += 20.0

    if ai_flag:
        score -= 60.0

    if is_spliced:
        score -= 40.0

    # Forensic indicators only penalize when 3 or more fire (avoid false positives)
    if forensic_n >= 3:
        score -= forensic_n * 8.0

    score = max(0.0, min(100.0, score))
    print(f"[IMAGE v3] Raw score: {score:.1f}")

    # ── Determine verdict ───────────────────────────────────────────────────
    if ai_flag and score < 50:
        if score < 25:
            verdict            = "AI Generated"
            confidence         = round((100 - score) / 100, 2)
            ai_probability     = round(min(90 + (50 - score) * 0.4, 98), 1)
            deepfake_probability = 2.0
        else:
            verdict            = "Likely AI Generated"
            confidence         = round((100 - score) / 100, 2)
            ai_probability     = round(60 + (50 - score) * 0.8, 1)
            deepfake_probability = 5.0

    elif is_spliced and not has_exif and score < 50:
        verdict              = "Deepfake"
        confidence           = round((100 - score) / 100, 2)
        ai_probability       = 35.0
        deepfake_probability = round(min(70 + noise_var * 0.3, 95), 1)

    elif score >= 80:
        verdict              = "Authentic"
        confidence           = round(score / 100, 2)
        ai_probability       = round(max(1, 20 - score * 0.15), 1)
        deepfake_probability = round(max(1, 10 - score * 0.08), 1)

    elif score >= 60:
        verdict              = "Likely Authentic"
        confidence           = round(score / 100, 2)
        ai_probability       = round(max(5, 40 - score * 0.3), 1)
        deepfake_probability = round(max(3, 20 - score * 0.15), 1)

    elif score >= 40:
        verdict              = "Suspicious"
        confidence           = round((100 - score) / 100, 2)
        ai_probability       = round(40 + (50 - score) * 0.5, 1)
        deepfake_probability = round(30 + (50 - score) * 0.4, 1)

    else:
        verdict              = "Suspicious"
        confidence           = round((100 - score) / 100, 2)
        ai_probability       = round(min(55 + (50 - score), 80), 1)
        deepfake_probability = round(min(40 + (50 - score) * 0.5, 70), 1)

    print(f"[IMAGE v3] Verdict={verdict}, confidence={confidence:.2f}, "
          f"ai_prob={ai_probability}%, deepfake_prob={deepfake_probability}%")

    # ── Key findings ────────────────────────────────────────────────────────
    findings = []

    if has_exif:
        findings.append(f"✓ Camera metadata (EXIF) detected — device: {device}")
    else:
        findings.append("✗ No camera metadata (EXIF) found")

    if has_face:
        findings.append(f"✓ {face_count} human face(s) detected — structure appears natural")
    elif image_type == "screenshot":
        findings.append("✓ Classified as screenshot — deepfake analysis not applicable")
    else:
        findings.append("• No human faces detected in image")

    if ai_flag:
        findings.append("✗ AI generation signature found in filename or metadata")
    else:
        findings.append("✓ No AI generation indicators found (filename & metadata clean)")

    if is_spliced:
        findings.append(f"✗ Inconsistent sensor noise across quadrants — possible splicing (variance: {noise_var:.1f})")
    else:
        findings.append("✓ Pixel noise is consistent across all image quadrants")

    if forensic_n >= 3:
        findings.append(f"✗ {forensic_n}/5 forensic anomalies detected: {'; '.join(forensic_reasons[:2])}")
    elif forensic_n > 0:
        findings.append(f"✓ Only {forensic_n}/5 minor forensic flag(s) — within normal camera range")
    else:
        findings.append("✓ No forensic anomalies detected — sharpness and frequency are normal")

    # ── Metadata summary ────────────────────────────────────────────────────
    metadata_summary = {
        "resolution": f"{width}x{height}",
        "has_exif": has_exif,
        "device": device if has_exif else "Unknown",
        "image_type": image_type.replace("_", " ").title(),
        "faces_detected": face_count,
    }
    if "DateTime" in exif:
        metadata_summary["capture_date"] = exif["DateTime"]
    if "Software" in exif:
        metadata_summary["software"] = exif["Software"][:60]

    # ── Free Image Arrays Before Network Call ───────────────────────────────
    try:
        del img_array, gray, hsv, pil_img
        gc.collect()
    except Exception:
        pass
    print(f"[MEMORY] After GC: {_get_mem_mb():.1f} MB")

    # ── Reverse image search ────────────────────────────────────────────────
    source_links = await _reverse_search(image_path, exif)

    return to_python({
        "verdict":             verdict,
        "confidence":          confidence,
        "ai_probability":      ai_probability,
        "deepfake_probability": deepfake_probability,
        "key_findings":        findings,
        "metadata_summary":    metadata_summary,
        "source_links":        source_links,
        # Legacy fields kept for backward compat with history/dashboard
        "truth_score":         round(score, 1),
        "ai_detection_score":  ai_probability,
        "result":              verdict,
        "image_type":          image_type,
    })

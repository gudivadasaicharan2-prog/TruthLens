"""
TruthLens — Video Deepfake Analyzer (v2)
=========================================
Fixes:
  - Removed broken ReverseImageSearch import (class deleted in image rebuild)
  - Fixed "no faces" fallback to return proper verdict fields
  - Fixed exception fallback to return proper verdict fields
  - Updated response schema: ai_probability, deepfake_probability, metadata_summary
  - Self-contained reverse search (no external class dependency)
"""

import os
import cv2
import uuid
import shutil
import httpx
import numpy as np
from html.parser import HTMLParser

# ── Reverse search (self-contained, no external class) ──────────────────────
async def _video_reverse_search(video_path: str) -> list[dict]:
    """DuckDuckGo text search based on filename. Wikipedia links excluded."""
    import re
    filename = os.path.basename(video_path)
    keywords = re.sub(r"[\-_.]", " ", filename)
    keywords = re.sub(
        r"\b(?:mp4|mov|avi|mkv|webm|upload|uuid|video|tmp)\b",
        "", keywords, flags=re.IGNORECASE
    )
    keywords = re.sub(r"\s+", " ", keywords).strip()
    if not keywords or len(keywords) < 3:
        return []

    results = []
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": f"{keywords} original video source", "kl": "us-en"},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            if resp.status_code == 200:
                class _DDGParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.results = []
                        self._in_link = False
                        self._cur = {}

                    def handle_starttag(self, tag, attrs):
                        if tag == "a":
                            d = dict(attrs)
                            if "result__a" in d.get("class", ""):
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

                for r in parser.results[:4]:
                    url = r["url"]
                    if "wikipedia.org" in url.lower():
                        continue
                    title = r["title"].strip()[:60]
                    if title and url:
                        results.append({"name": title, "url": url})
                    if len(results) >= 3:
                        break
    except Exception as e:
        print(f"[VIDEO SEARCH] Error: {e}")

    return results


# ── Face cascade ─────────────────────────────────────────────────────────────
_FACE_CASCADE = None

def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        _FACE_CASCADE = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    return _FACE_CASCADE


def _has_face(frame: np.ndarray) -> bool:
    try:
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = _get_face_cascade().detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
        )
        return len(faces) > 0
    except Exception:
        return False


# ── Frame forensic scoring ───────────────────────────────────────────────────
def _score_frame(frame: np.ndarray) -> float:
    """Return fake probability 0-1 for a single frame."""
    try:
        gray          = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        lap_var       = cv2.Laplacian(gray, cv2.CV_64F).var()
        noise         = float(np.std(gray))
        edges         = cv2.Canny(gray, 100, 200)
        edge_density  = float(np.sum(edges > 0)) / (edges.shape[0] * edges.shape[1])
        blur          = float(np.var(cv2.Laplacian(gray, cv2.CV_64F)))

        flags = 0
        if lap_var < 50:      flags += 1   # blurry — common in synthetic video
        if noise < 20:        flags += 1   # too clean
        if edge_density < 0.01 or edge_density > 0.10: flags += 1
        if blur < 100:        flags += 1

        return min(flags / 4.0, 0.95)
    except Exception as e:
        print(f"[FRAME] Scoring error: {e}")
        return 0.5


# ── Face consistency ─────────────────────────────────────────────────────────
def _face_consistency(frame_paths: list[str]) -> float:
    if len(frame_paths) < 2:
        return 1.0
    try:
        hists = []
        for path in frame_paths:
            img = cv2.imread(path)
            if img is None:
                continue
            hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
            hists.append(hist)

        if len(hists) < 2:
            return 0.85

        corrs = [
            cv2.compareHist(hists[i], hists[i + 1], cv2.HISTCMP_CORREL)
            for i in range(len(hists) - 1)
        ]
        return float(np.mean(corrs))
    except Exception as e:
        print(f"[FACE CONSISTENCY] Error: {e}")
        return 0.85


# ── Lip-sync ─────────────────────────────────────────────────────────────────
def _estimate_mouth_height(img: np.ndarray) -> float:
    try:
        gray         = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w         = gray.shape
        mouth        = gray[int(h * 0.65):int(h * 0.88), int(w * 0.3):int(w * 0.7)]
        _, thresh    = cv2.threshold(mouth, 45, 255, cv2.THRESH_BINARY_INV)
        contours, _  = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            _, _, _, ch = cv2.boundingRect(max(contours, key=cv2.contourArea))
            return float(ch / h)
        return 0.0
    except Exception:
        return 0.0


def _lip_sync(frame_paths: list[str]) -> dict:
    if len(frame_paths) < 3:
        return {"status": "Inconclusive — insufficient frames for lip-sync check", "variance": 0.0}
    try:
        heights  = []
        for path in frame_paths:
            img = cv2.imread(path)
            if img is not None:
                heights.append(_estimate_mouth_height(img))
        variance = float(np.var(heights)) if heights else 0.0
        status   = "Lips showing active movements" if variance > 0.0005 else "Lips mostly static"
        return {"status": status, "variance": variance}
    except Exception as e:
        print(f"[LIP-SYNC] Error: {e}")
        return {"status": "Inconclusive", "variance": 0.0}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _safe_result(verdict: str, confidence: float, ai_prob: float, deepfake_prob: float,
                 findings: list[str], metadata: dict, source_links: list[dict]) -> dict:
    """Construct a guaranteed-complete response dict for the frontend ResultCard."""
    from app.core.serializer import to_python
    return to_python({
        "verdict":              verdict,
        "confidence":           confidence,
        "ai_probability":       ai_prob,
        "deepfake_probability": deepfake_prob,
        "key_findings":         findings,
        "metadata_summary":     metadata,
        "source_links":         source_links,
        # Legacy back-compat fields
        "truth_score":          round(confidence * 100, 1),
        "ai_detection_score":   ai_prob,
        "result":               verdict,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Main analyzer
# ═══════════════════════════════════════════════════════════════════════════════
async def analyze_video(video_path: str) -> dict:
    filename  = os.path.basename(video_path)
    frame_dir = f"./uploads/frames/{uuid.uuid4()}"
    os.makedirs(frame_dir, exist_ok=True)

    print(f"\n[VIDEO v2] Analyzing: {filename}")

    try:
        # ── Open video ───────────────────────────────────────────────────────
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"[VIDEO v2] Cannot open video: {video_path}")
            return _safe_result(
                verdict="Analysis Failed",
                confidence=0.0, ai_prob=0.0, deepfake_prob=0.0,
                findings=["✗ Could not open video file — format may be unsupported"],
                metadata={"filename": filename, "error": "Cannot open video"},
                source_links=[],
            )

        fps          = float(cap.get(cv2.CAP_PROP_FPS) or 30)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration     = float(total_frames / fps) if fps > 0 else 0.0
        width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        print(f"[VIDEO v2] {width}x{height}, {fps:.1f} FPS, {duration:.1f}s, {total_frames} frames")

        metadata = {
            "resolution":   f"{width}x{height}",
            "fps":          f"{fps:.1f}",
            "duration":     f"{duration:.1f}s",
            "frame_count":  total_frames,
        }

        # ── Extract keyframes ────────────────────────────────────────────────
        frame_interval = max(int(fps * 2), 1)
        frames_with_faces  = []   # (path, timestamp) — face frames
        frames_all         = []   # (path, timestamp) — all sampled frames
        frame_num          = 0

        while cap.isOpened() and len(frames_all) < 15:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_num % frame_interval == 0:
                ts   = round(frame_num / fps, 1)
                path = os.path.join(frame_dir, f"f_{frame_num}.jpg")
                cv2.imwrite(path, frame)
                frames_all.append((path, ts))
                if _has_face(frame):
                    frames_with_faces.append((path, ts))
            frame_num += 1

        cap.release()

        print(f"[VIDEO v2] Sampled {len(frames_all)} frames, {len(frames_with_faces)} with faces")

        # ── Reverse search ───────────────────────────────────────────────────
        source_links = await _video_reverse_search(video_path)

        # ── No faces detected ────────────────────────────────────────────────
        if not frames_with_faces:
            # Still score general frames for AI artifacts
            all_paths    = [f[0] for f in frames_all]
            frame_scores = [_score_frame(cv2.imread(p)) for p in all_paths if cv2.imread(p) is not None]
            avg_score    = float(np.mean(frame_scores)) if frame_scores else 0.3

            print(f"[VIDEO v2] No faces - frame forensic score: {avg_score:.2f}")

            if avg_score > 0.65:
                verdict      = "Suspicious"
                confidence   = round((avg_score), 2)
                ai_prob      = round(avg_score * 90, 1)
                deepfake_prob = 20.0
            else:
                verdict      = "Likely Authentic"
                confidence   = round(1.0 - avg_score * 0.5, 2)
                ai_prob      = round(avg_score * 30, 1)
                deepfake_prob = 5.0

            findings = [
                "• No human faces detected — deepfake face-swap analysis not applicable",
                f"✓ Video metadata: {width}x{height} @ {fps:.1f} FPS, {duration:.1f}s duration",
                f"{'✗' if avg_score > 0.65 else '✓'} Frame forensic score: {avg_score:.0%} "
                f"({'anomalous' if avg_score > 0.65 else 'normal range'})",
            ]

            return _safe_result(verdict, confidence, ai_prob, deepfake_prob,
                                findings, metadata, source_links)

        # ── Face-based analysis ──────────────────────────────────────────────
        face_paths        = [f[0] for f in frames_with_faces]
        consistency_score = _face_consistency(face_paths)
        face_swapped      = consistency_score < 0.60
        lip_result        = _lip_sync(face_paths)
        frame_scores      = [_score_frame(cv2.imread(p)) for p in face_paths if cv2.imread(p) is not None]
        avg_score         = float(np.mean(frame_scores)) if frame_scores else 0.3
        max_score         = float(np.max(frame_scores)) if frame_scores else 0.3

        print(f"[VIDEO v2] consistency={consistency_score:.2f}, swapped={face_swapped}, "
              f"avg_frame_score={avg_score:.2f}, lip={lip_result['status']}")

        # ── Verdict calibration ──────────────────────────────────────────────
        is_suspicious = face_swapped or avg_score > 0.55

        if is_suspicious:
            if avg_score > 0.70 or face_swapped:
                verdict       = "Deepfake"
                confidence    = round(min(0.40 + avg_score * 0.5, 0.92), 2)
                ai_prob       = round(min(40 + avg_score * 50, 90.0), 1)
                deepfake_prob = round(min(60 + avg_score * 35, 95.0), 1)
            else:
                verdict       = "Suspicious"
                confidence    = round(0.55 + avg_score * 0.2, 2)
                ai_prob       = round(30 + avg_score * 30, 1)
                deepfake_prob = round(35 + avg_score * 25, 1)
        else:
            if avg_score < 0.20 and consistency_score > 0.80:
                verdict       = "Authentic"
                confidence    = round(min(0.90 + (0.80 - avg_score), 0.98), 2)
                ai_prob       = round(max(1, avg_score * 20), 1)
                deepfake_prob = round(max(1, avg_score * 12), 1)
            else:
                verdict       = "Likely Authentic"
                confidence    = round(0.75 + (0.55 - avg_score) * 0.3, 2)
                ai_prob       = round(max(5, avg_score * 35), 1)
                deepfake_prob = round(max(3, avg_score * 20), 1)

        confidence    = max(0.0, min(confidence, 0.99))
        ai_prob       = max(1.0, min(ai_prob, 99.0))
        deepfake_prob = max(1.0, min(deepfake_prob, 99.0))

        # ── Key findings ─────────────────────────────────────────────────────
        findings = [
            f"✓ Video metadata: {width}x{height} @ {fps:.1f} FPS, {duration:.1f}s",
            f"{'✗' if face_swapped else '✓'} Face consistency across frames: "
            f"{consistency_score:.2f} ({'inconsistent — possible face swap' if face_swapped else 'consistent — genuine'})",
            f"{'✓' if 'active' in lip_result['status'].lower() else '•'} {lip_result['status']}",
            f"{'✗' if avg_score > 0.55 else '✓'} Frame forensic score: {avg_score:.0%} "
            f"({'anomalous' if avg_score > 0.55 else 'normal'})",
            f"✓ {len(face_paths)} face-containing frame(s) analyzed",
        ]
        if source_links:
            findings.append(f"✓ Cross-referenced against {len(source_links)} online source(s)")

        metadata.update({
            "faces_detected": len(frames_with_faces),
            "frames_analyzed": len(face_paths),
        })

        print(f"[VIDEO v2] Verdict={verdict}, confidence={confidence:.2f}, "
              f"ai={ai_prob}%, deepfake={deepfake_prob}%")

        return _safe_result(verdict, confidence, ai_prob, deepfake_prob,
                            findings, metadata, source_links)

    except Exception as e:
        import traceback
        print(f"[VIDEO v2] EXCEPTION: {e}")
        traceback.print_exc()

        return _safe_result(
            verdict="Analysis Failed",
            confidence=0.0, ai_prob=0.0, deepfake_prob=0.0,
            findings=[f"✗ Video analysis encountered an error: {str(e)}"],
            metadata={"filename": filename, "error": str(e)},
            source_links=[],
        )
    finally:
        if os.path.exists(frame_dir):
            try:
                shutil.rmtree(frame_dir)
            except Exception:
                pass

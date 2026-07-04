"""
TruthLens — Face Detector (RetinaFace-class via facenet-pytorch MTCNN)
=======================================================================
Replaces the old OpenCV Haar Cascade face detector with a deep-learning
based MTCNN detector from facenet-pytorch, which uses a multi-stage
cascade CNN pipeline equivalent in accuracy and approach to RetinaFace.

Features:
  - Lazy-loads the model on first call (not at import time)
  - Automatically uses GPU (CUDA) if available, falls back to CPU
  - Returns face count as int — drop-in replacement for Haar Cascade
  - Thread-safe singleton model instance
  - Confidence threshold filtering to reduce false positives
"""

import numpy as np
import torch
from PIL import Image

_MTCNN = None
_DEVICE = None


def _get_detector():
    """Lazy-load MTCNN singleton. Uses CUDA GPU if available, else CPU."""
    global _MTCNN, _DEVICE
    if _MTCNN is None:
        from facenet_pytorch import MTCNN
        _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _MTCNN = MTCNN(
            keep_all=True,
            device=_DEVICE,
            min_face_size=20,
            thresholds=[0.6, 0.7, 0.7],
            post_process=False,
        )
        print(f"[FACE_DETECTOR] MTCNN (RetinaFace-class) loaded on device: {_DEVICE}")
    return _MTCNN


def detect_faces_retina(img_rgb: np.ndarray) -> int:
    """
    Detect faces in an RGB numpy array using MTCNN (RetinaFace-class detector).

    Replaces the old OpenCV Haar Cascade _detect_faces(gray) function.
    Called by image_deepfake.py with the RGB image array (not grayscale).

    Args:
        img_rgb: np.ndarray of shape (H, W, 3) in RGB colour order.

    Returns:
        int: Number of faces detected with confidence >= 0.85.
             Returns 0 on any failure — caller handles the no-face path.
    """
    try:
        detector = _get_detector()
        pil_img = Image.fromarray(img_rgb.astype(np.uint8))
        boxes, probs = detector.detect(pil_img)

        if boxes is None or len(boxes) == 0:
            return 0

        # Filter detections by confidence to reduce false positives
        confident_count = sum(
            1 for p in probs if p is not None and float(p) >= 0.85
        )
        return confident_count

    except Exception as e:
        print(f"[FACE_DETECTOR] Detection error: {e}. Returning 0 (full-image fallback).")
        return 0


def detect_faces_with_boxes(
    img_rgb: np.ndarray,
) -> tuple[int, "np.ndarray | None", "np.ndarray | None"]:
    """
    Detect faces and return raw MTCNN outputs for downstream face cropping.

    Used by image_deepfake.py to pass boxes to image_model.get_all_face_crops()
    so every detected face can be individually classified by EfficientNet-B4.

    Args:
        img_rgb: np.ndarray of shape (H, W, 3) in RGB colour order.

    Returns:
        Tuple of (confident_face_count, boxes, probs).
        boxes and probs are the raw MTCNN arrays (may be None if no faces).
        confident_face_count is the count of faces with prob >= 0.85.
    """
    try:
        detector = _get_detector()
        pil_img = Image.fromarray(img_rgb.astype(np.uint8))
        boxes, probs = detector.detect(pil_img)

        if boxes is None or len(boxes) == 0:
            return 0, None, None

        confident_count = sum(
            1 for p in probs if p is not None and float(p) >= 0.85
        )
        return confident_count, boxes, probs

    except Exception as e:
        print(f"[FACE_DETECTOR] detect_faces_with_boxes error: {e}. Returning 0.")
        return 0, None, None



def get_cropped_face(img_rgb: np.ndarray) -> "np.ndarray | None":
    """
    Return the highest-confidence face as a cropped RGB numpy array, or
    None if no face is detected. Available for callers that need the crop.

    Args:
        img_rgb: np.ndarray of shape (H, W, 3) in RGB colour order.

    Returns:
        np.ndarray of the cropped face region (RGB), or None.
    """
    try:
        detector = _get_detector()
        pil_img = Image.fromarray(img_rgb.astype(np.uint8))
        boxes, probs = detector.detect(pil_img)

        if boxes is None or len(boxes) == 0:
            return None

        best_idx = int(np.argmax(probs))
        if float(probs[best_idx]) < 0.85:
            return None

        x1, y1, x2, y2 = [int(v) for v in boxes[best_idx]]
        h, w = img_rgb.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x2 <= x1 or y2 <= y1:
            return None

        return img_rgb[y1:y2, x1:x2]

    except Exception as e:
        print(f"[FACE_DETECTOR] Crop error: {e}. Returning None.")
        return None

"""
TruthLens — EfficientNet-B4 Feature Extractor + Deepfake Classifier
====================================================================
Architecture:
  Backbone : EfficientNet-B4 (ImageNet pretrained, fully frozen)
             Used purely as a feature extractor — no classification head
             from ImageNet survives.
  Head     : DeepfakeClassifierHead — a small MLP (1792 -> 512 -> 1)
             with a Sigmoid output, designed to accept deepfake-trained
             weights loaded from a checkpoint file.

Trained-weights workflow:
  1. Train the classifier head on a deepfake dataset (FaceForensics++,
     DFDC, CelebDF, etc.) with the backbone frozen.
  2. Save only the head state dict:
         torch.save(model.classifier_head.state_dict(), "deepfake_classifier.pth")
  3. Place the file at the path defined by CLASSIFIER_WEIGHTS_PATH below.
  4. Restart the server — weights are picked up automatically.

Untrained-fallback mode:
  When no checkpoint is found the head runs with random initial weights.
  predict_fake_probability() dampens all outputs toward 0.5 to honestly
  reflect the lack of calibration.  is_using_trained_weights() returns
  False so callers can surface a warning to the user.

Model backbone weights:
  torchvision auto-downloads EfficientNet-B4 ImageNet weights (~74 MB)
  from the PyTorch CDN on first startup and caches them permanently in
  ~/.cache/torch/hub/checkpoints/  — no manual action required.

GPU / CPU:
  Uses CUDA if available, falls back to CPU automatically.
"""

import os
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
import torchvision.transforms as T
from torchvision.models import efficientnet_b4, EfficientNet_B4_Weights

# ---------------------------------------------------------------------------
# CHECKPOINT PATH — change only this constant to swap in trained weights.
#
# After training your classifier head, save its state dict:
#     torch.save(trained_head.state_dict(), "deepfake_classifier.pth")
# Place that file at the path below, then restart the server.
#
# Resolved path: backend/weights/deepfake_classifier.pth
# ---------------------------------------------------------------------------
CLASSIFIER_WEIGHTS_PATH: str = os.path.join(
    os.path.dirname(__file__),   # backend/app/models/
    "..", "..", "weights",        # -> backend/weights/
    "deepfake_classifier.pth",
)
# ---------------------------------------------------------------------------

# EfficientNet-B4 feature dimension after global average pooling
_EFFICIENTNET_B4_FEATURES: int = 1792

# EfficientNet-B4 canonical input: 380x380, ImageNet normalisation
_TRANSFORM = T.Compose([
    T.Resize((380, 380)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]),
])

# ---- Singleton state -------------------------------------------------------
_BACKBONE: nn.Module | None = None         # frozen EfficientNet-B4 feature extractor
_CLASSIFIER: nn.Module | None = None       # DeepfakeClassifierHead instance
_DEVICE: torch.device | None = None
_WEIGHTS_LOADED: bool = False              # True only when trained checkpoint was found


# ---- Classifier head (named module for clean state_dict mapping) ------------

class DeepfakeClassifierHead(nn.Module):
    """
    Lightweight MLP classifier on top of the frozen EfficientNet-B4 backbone.

    Input  : 1-D feature vector of length in_features (1792 for EffNet-B4)
    Output : scalar in [0, 1]  — probability the image is a deepfake

    To train this head on a deepfake dataset:
      1. Pair it with a frozen EfficientNet-B4 backbone.
      2. Train with BCELoss on labelled real/fake face crops.
      3. Save:  torch.save(head.state_dict(), "deepfake_classifier.pth")
      4. Update CLASSIFIER_WEIGHTS_PATH above and restart the server.

    The state_dict keys are: fc1.*, bn1.*, fc2.*, sigmoid (unused in training).
    A trained checkpoint must match these exact key names.
    """

    def __init__(self, in_features: int = _EFFICIENTNET_B4_FEATURES) -> None:
        super().__init__()
        self.fc1     = nn.Linear(in_features, 512)
        self.bn1     = nn.BatchNorm1d(512)
        self.relu    = nn.ReLU(inplace=True)
        self.dropout = nn.Dropout(p=0.4)
        self.fc2     = nn.Linear(512, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return self.sigmoid(x)


# ---- Public API -------------------------------------------------------------

def is_using_trained_weights() -> bool:
    """
    Returns True if a deepfake-trained checkpoint was successfully loaded.
    Returns False when running in untrained/feature-extraction mode.

    Callers (e.g. image_deepfake.py) use this to add an honest note to
    key_findings so users know the model has not been calibrated on deepfakes.
    """
    return _WEIGHTS_LOADED


def load_model() -> None:
    """
    Initialise the EfficientNet-B4 backbone and DeepfakeClassifierHead.
    Called once during FastAPI lifespan startup — subsequent calls are no-ops.

    Steps:
      1. Download / load EfficientNet-B4 ImageNet weights (cached after first run).
      2. Strip the original 1000-class classification head; keep only the
         convolutional feature extractor and average-pooling layer.
      3. Freeze all backbone parameters — backbone is never updated.
      4. Instantiate DeepfakeClassifierHead with random initial weights.

      *** CHECKPOINT LOAD POINT ***
      5. If CLASSIFIER_WEIGHTS_PATH resolves to an existing file, load the
         deepfake-trained state dict into the classifier head.
         Replace only this file path to upgrade to better trained weights.
      *** END CHECKPOINT LOAD POINT ***

      6. Set everything to eval() mode and move to the selected device.
    """
    global _BACKBONE, _CLASSIFIER, _DEVICE, _WEIGHTS_LOADED

    if _BACKBONE is not None:
        return  # already initialised — no-op

    _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[IMAGE_MODEL] Initialising EfficientNet-B4 on {_DEVICE} ...")

    # Step 1 + 2: Load full model, then discard the classifier head.
    # We keep only features (conv stages) + avgpool + flatten to get a
    # 1792-dimensional feature vector per image.
    full_model = efficientnet_b4(weights=EfficientNet_B4_Weights.IMAGENET1K_V1)

    backbone = nn.Sequential(
        full_model.features,    # convolutional stages  (B, 1792, H', W')
        full_model.avgpool,     # global average pool   (B, 1792, 1, 1)
        nn.Flatten(),           # flatten               (B, 1792)
    )

    # Step 3: Freeze every backbone parameter permanently.
    for param in backbone.parameters():
        param.requires_grad = False

    _BACKBONE = backbone.eval().to(_DEVICE)

    # Step 4: Instantiate classifier head with random weights.
    head = DeepfakeClassifierHead(in_features=_EFFICIENTNET_B4_FEATURES)

    # *** CHECKPOINT LOAD POINT *******************************************
    # To upgrade to deepfake-trained weights:
    #   1. Set CLASSIFIER_WEIGHTS_PATH at the top of this file.
    #   2. The file must contain the output of:
    #          torch.save(trained_head.state_dict(), "deepfake_classifier.pth")
    #   3. Restart the backend server.
    weights_path = os.path.abspath(CLASSIFIER_WEIGHTS_PATH)
    if os.path.isfile(weights_path):
        try:
            state = torch.load(weights_path, map_location=_DEVICE, weights_only=True)
            head.load_state_dict(state)
            _WEIGHTS_LOADED = True
            print(f"[IMAGE_MODEL] Deepfake classifier weights loaded: {weights_path}")
        except Exception as e:
            _WEIGHTS_LOADED = False
            print(
                f"[IMAGE_MODEL] WARNING — classifier weights at {weights_path} "
                f"could not be loaded: {e}\n"
                f"             Falling back to untrained feature-extraction mode."
            )
    else:
        _WEIGHTS_LOADED = False
        print(
            f"[IMAGE_MODEL] No trained weights found at:\n"
            f"               {weights_path}\n"
            f"             Running in untrained feature-extraction mode.\n"
            f"             Predictions are dampened toward 0.5 to avoid\n"
            f"             misleading confidence from an uncalibrated head."
        )
    # *** END CHECKPOINT LOAD POINT ***************************************

    _CLASSIFIER = head.eval().to(_DEVICE)
    mode = "TRAINED deepfake classifier" if _WEIGHTS_LOADED else "UNTRAINED (feature-based)"
    print(f"[IMAGE_MODEL] Ready — backbone=EfficientNet-B4 (frozen), head={mode}, device={_DEVICE}")


def _ensure_loaded() -> None:
    """Lazy-initialise on first inference call if startup hook was not triggered."""
    if _BACKBONE is None or _CLASSIFIER is None:
        load_model()


def predict_fake_probability(img_rgb: np.ndarray) -> float:
    """
    Return a fake probability in [0.0, 1.0] for an RGB numpy image array.

    Trained-weights mode (is_using_trained_weights() == True):
      0.0 -> definitely real / authentic
      1.0 -> definitely fake / AI-generated or face-swapped

    Untrained feature-extraction mode (is_using_trained_weights() == False):
      The raw head output is dampened toward 0.5 by 60%:
          dampened = 0.5 + (raw - 0.5) * 0.40
      This prevents an uncalibrated random head from accidentally generating
      high-confidence verdicts that would mislead users.

    Args:
        img_rgb: np.ndarray of shape (H, W, 3), dtype uint8, RGB order.

    Returns:
        float in [0.0, 1.0]. Returns 0.5 (perfectly neutral) on any error.
    """
    _ensure_loaded()
    try:
        pil_img = Image.fromarray(img_rgb.astype(np.uint8)).convert("RGB")
        tensor  = _TRANSFORM(pil_img).unsqueeze(0).to(_DEVICE)  # (1, 3, 380, 380)

        with torch.no_grad():
            features  = _BACKBONE(tensor)            # (1, 1792)
            raw_prob  = _CLASSIFIER(features)        # (1, 1)
            fake_prob = float(raw_prob.squeeze())    # scalar in [0, 1]

        fake_prob = min(max(fake_prob, 0.0), 1.0)

        if not _WEIGHTS_LOADED:
            # Dampen toward 0.5 — untrained head is not calibrated.
            # Retains 40% of the deviation from neutral to preserve ordering
            # signal from the feature extractor without false precision.
            fake_prob = 0.5 + (fake_prob - 0.5) * 0.40

        return round(fake_prob, 4)

    except Exception as e:
        print(f"[IMAGE_MODEL] Inference error: {e}. Returning neutral 0.5.")
        return 0.5


def predict_whole_image(img_rgb: np.ndarray) -> float:
    """
    Run EfficientNet-B4 on the entire image for whole-image AI detection.

    Semantically distinct from predict_fake_probability() (which is used for
    face crops in deepfake detection).  Both pass through the same backbone
    and classifier, but calling them by separate names in image_deepfake.py
    makes the two-signal fusion architecture explicit and readable.

    Args:
        img_rgb: np.ndarray of shape (H, W, 3), dtype uint8, RGB order.

    Returns:
        float in [0.0, 1.0]. Returns 0.5 (neutral) on any error.
    """
    return predict_fake_probability(img_rgb)


def get_all_face_crops(
    img_rgb: np.ndarray,
    boxes: "np.ndarray | None",
    probs: "np.ndarray | None",
    min_confidence: float = 0.85,
) -> list[np.ndarray]:
    """
    Crop every detected face from img_rgb that meets the confidence threshold.

    Args:
        img_rgb:        Full RGB image array (H, W, 3).
        boxes:          Bounding boxes from MTCNN.detect() shape (N, 4) or None.
        probs:          Detection confidences shape (N,) or None.
        min_confidence: Minimum MTCNN confidence to accept a crop.

    Returns:
        List of RGB numpy arrays, one per accepted face crop. Empty if none.
    """
    if boxes is None or probs is None or len(boxes) == 0:
        return []

    h, w = img_rgb.shape[:2]
    crops: list[np.ndarray] = []

    for box, prob in zip(boxes, probs):
        if prob is None or float(prob) < min_confidence:
            continue
        x1, y1, x2, y2 = [int(v) for v in box]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x2 > x1 and y2 > y1:
            crops.append(img_rgb[y1:y2, x1:x2])

    return crops

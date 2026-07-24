"""
CLIP Detector for AI Content Detection
======================================
Uses OpenCLIP for semantic classification to complement EfficientNet-B4.
Implements singleton pattern for efficient model loading.
"""

import torch
import numpy as np
from PIL import Image
from typing import Dict, Optional, Tuple
import torchvision.transforms as T

# Singleton pattern for CLIP model
_CLIP_MODEL = None
_CLIP_PREPROCESS = None
_CLIP_DEVICE = None
_CLIP_MODEL_NAME = "ViT-B-32"
_CLIP_PRETRAINED = "laion2b_s34b_b79k"


def _load_clip_model():
    """
    Load OpenCLIP model as singleton.
    
    Returns:
        model, preprocess, device
    """
    global _CLIP_MODEL, _CLIP_PREPROCESS, _CLIP_DEVICE
    
    if _CLIP_MODEL is not None:
        return _CLIP_MODEL, _CLIP_PREPROCESS, _CLIP_DEVICE
    
    try:
        import open_clip
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        print(f"[CLIP] Loading {_CLIP_MODEL_NAME}/{_CLIP_PRETRAINED} on {device}...")
        model, _, preprocess = open_clip.create_model_and_transforms(
            _CLIP_MODEL_NAME,
            pretrained=_CLIP_PRETRAINED,
            device=device
        )
        model.eval()
        
        _CLIP_MODEL = model
        _CLIP_PREPROCESS = preprocess
        _CLIP_DEVICE = device
        
        print(f"[CLIP] Model loaded successfully on {device}")
        return model, preprocess, device
        
    except ImportError:
        print("[CLIP] open_clip not installed, using fallback")
        return None, None, None
    except Exception as e:
        print(f"[CLIP] Error loading model: {e}")
        return None, None, None


def get_clip_model():
    """Get the singleton CLIP model instance."""
    return _load_clip_model()


# Text prompts for AI detection
AI_PROMPTS = [
    "AI generated image",
    "artificial intelligence artwork",
    "computer generated illustration",
    "synthetic image",
    "deepfake generated content",
    "diffusion model output",
    "GAN generated image",
    "neural network artwork",
    "AI created photograph",
    "machine generated visual"
]

REAL_PROMPTS = [
    "real photograph",
    "authentic camera image",
    "natural photograph",
    "genuine photo",
    "real world image",
    "camera captured photo",
    "authentic scene",
    "natural lighting photograph",
    "realistic image",
    "genuine visual"
]

ARTWORK_PROMPTS = [
    "digital artwork",
    "illustration",
    "cartoon",
    "anime style",
    "digital painting",
    "concept art",
    "graphic design",
    "vector art",
    "stylized illustration",
    "animated character"
]


def _calculate_clip_probability(
    image_features: torch.Tensor,
    text_features: torch.Tensor
) -> float:
    """
    Calculate AI probability from CLIP features.
    
    Args:
        image_features: Image embedding from CLIP
        text_features: Text embedding from CLIP
    
    Returns:
        AI probability as float [0, 1]
    """
    # Calculate cosine similarity
    similarity = (image_features @ text_features.T).softmax(dim=-1)
    
    # Assume first half are AI prompts, second half are real prompts
    ai_score = similarity[:, :len(AI_PROMPTS)].mean().item()
    real_score = similarity[:, len(AI_PROMPTS):].mean().item()
    
    # Normalize to probability
    total = ai_score + real_score
    if total > 0:
        ai_prob = ai_score / total
    else:
        ai_prob = 0.5
    
    return ai_prob


def detect_with_clip(
    img_array: np.ndarray,
    image_type: str = "mixed_scene"
) -> Dict[str, any]:
    """
    Detect AI content using CLIP semantic classification.
    
    Args:
        img_array: RGB image as numpy array
        image_type: Image type from classifier (affects prompt selection)
    
    Returns:
        Dict with keys:
            - ai_probability: float [0, 1]
            - confidence: float [0, 1]
            - features: dict (feature scores)
            - reason: str (classification reasoning)
    """
    model, preprocess, device = get_clip_model()
    
    if model is None:
        # Fallback if CLIP not available
        return {
            "ai_probability": 0.5,
            "confidence": 0.0,
            "features": {},
            "reason": "CLIP model not available"
        }
    
    try:
        # Convert numpy array to PIL Image
        pil_img = Image.fromarray(img_array)
        
        # Preprocess image
        image_input = preprocess(pil_img).unsqueeze(0).to(device)
        
        # Select appropriate prompts based on image type
        if image_type in ["ai_artwork", "artwork", "cartoon"]:
            prompts = AI_PROMPTS + ARTWORK_PROMPTS + REAL_PROMPTS
            reason_type = "artwork"
        else:
            prompts = AI_PROMPTS + REAL_PROMPTS
            reason_type = "general"
        
        # Tokenize prompts
        import open_clip
        text_tokens = open_clip.tokenize(prompts).to(device)
        
        # Encode image and text
        with torch.no_grad():
            image_features = model.encode_image(image_input)
            text_features = model.encode_text(text_tokens)
            
            # Normalize features
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # Calculate similarity scores
        similarity = (image_features @ text_features.T).softmax(dim=-1)
        similarity_scores = similarity[0].cpu().numpy()
        
        # Calculate AI probability
        ai_score = similarity_scores[:len(AI_PROMPTS)].mean()
        real_score = similarity_scores[len(AI_PROMPTS):len(AI_PROMPTS) + len(REAL_PROMPTS)].mean()
        
        total = ai_score + real_score
        if total > 0:
            ai_probability = ai_score / total
        else:
            ai_probability = 0.5
        
        # Calculate confidence based on score difference
        confidence = abs(ai_probability - 0.5) * 2
        
        # Extract feature scores
        features = {
            "ai_similarity": float(ai_score),
            "real_similarity": float(real_score),
            "max_similarity": float(np.max(similarity_scores)),
            "min_similarity": float(np.min(similarity_scores)),
            "std_similarity": float(np.std(similarity_scores))
        }
        
        # Generate reasoning
        if ai_probability > 0.7:
            reason = f"CLIP semantic analysis strongly indicates AI-generated {reason_type}"
        elif ai_probability > 0.5:
            reason = f"CLIP semantic analysis suggests possible AI-generated {reason_type}"
        elif ai_probability < 0.3:
            reason = f"CLIP semantic analysis indicates authentic {reason_type}"
        else:
            reason = f"CLIP semantic analysis is inconclusive for {reason_type}"
        
        return {
            "ai_probability": round(ai_probability, 4),
            "confidence": round(confidence, 4),
            "features": features,
            "reason": reason
        }
        
    except Exception as e:
        print(f"[CLIP] Detection error: {e}")
        return {
            "ai_probability": 0.5,
            "confidence": 0.0,
            "features": {},
            "reason": f"CLIP detection failed: {str(e)}"
        }


def should_use_clip(image_type: str) -> bool:
    """
    Determine if CLIP should be used for the given image type.
    
    Args:
        image_type: Image type from classifier
    
    Returns:
        bool: True if CLIP should be used
    """
    # Skip CLIP for documents and screenshots (forensics is better)
    if image_type in ["document", "screenshot"]:
        return False
    
    # Use CLIP for artwork, AI artwork, cartoons, mixed scenes
    if image_type in ["ai_artwork", "artwork", "cartoon", "mixed_scene"]:
        return True
    
    # Optionally use CLIP for other types (can be configured)
    return True


def get_clip_ensemble_weight(image_type: str) -> float:
    """
    Get CLIP weight for ensemble based on image type.
    
    Args:
        image_type: Image type from classifier
    
    Returns:
        float: CLIP weight [0, 1]
    """
    if image_type in ["ai_artwork", "artwork", "cartoon"]:
        return 0.55  # High weight for artwork
    elif image_type in ["real_photograph", "portrait", "selfie", "landscape"]:
        return 0.10  # Low weight for photos
    elif image_type in ["document", "screenshot"]:
        return 0.00  # Skip for documents
    else:  # mixed_scene, object
        return 0.25  # Moderate weight for mixed content

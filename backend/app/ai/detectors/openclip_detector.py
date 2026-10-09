"""
OpenCLIP AI Artwork Detector for TruthLens v3.0
================================================
Uses OpenCLIP with ViT-B-32 for fast semantic analysis of AI-generated artwork.
Compares images against specific prompts for real photographs vs AI generators.
"""

import numpy as np
from typing import Dict, Tuple, Optional
import torch

# Global model cache
_MODEL = None
_PREPROCESS = None
_DEVICE = None


def _get_model():
    """Lazy load OpenCLIP model with global caching."""
    global _MODEL, _PREPROCESS, _DEVICE
    
    if _MODEL is None:
        try:
            import open_clip
            
            print("[OPENCLIP] Loading ViT-B-32 model...")
            _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
            # Load ViT-B-32 model (lightweight, fast)
            model_name = 'ViT-B-32'
            pretrained = 'laion2b_s34b_b79k'
            
            _MODEL, _, _PREPROCESS = open_clip.create_model_and_transforms(
                model_name, 
                pretrained=pretrained,
                device=_DEVICE
            )
            _MODEL.eval()
            
            print(f"[OPENCLIP] Model loaded on {_DEVICE}")
        except ImportError:
            print("[OPENCLIP] ERROR: open_clip_torch not installed")
            _MODEL = None
            _PREPROCESS = None
            _DEVICE = None
        except Exception as e:
            print(f"[OPENCLIP] ERROR: Failed to load model: {e}")
            _MODEL = None
            _PREPROCESS = None
            _DEVICE = None
    
    return _MODEL, _PREPROCESS, _DEVICE


# Semantic prompts for real photographs
REAL_PHOTO_PROMPTS = [
    "a real camera photograph",
    "a DSLR photograph",
    "a smartphone photograph",
    "a scanned photograph",
    "a human captured photo"
]

# Semantic prompts for AI-generated images
AI_GENERATOR_PROMPTS = [
    "an AI generated image",
    "a ChatGPT GPT Image",
    "a DALL-E 3 image",
    "a Midjourney artwork",
    "a Stable Diffusion image",
    "a FLUX generated image",
    "an Imagen generated image",
    "an AI illustration",
    "an AI anime artwork",
    "an AI digital painting",
    "a synthetic image",
    "a computer generated illustration",
    "a human drawn artwork"
]


def _compute_cosine_similarity(
    image_features: torch.Tensor,
    text_features: torch.Tensor
) -> np.ndarray:
    """
    Compute cosine similarity between image and text features.
    
    Args:
        image_features: Image feature tensor (1, D)
        text_features: Text feature tensor (N, D)
    
    Returns:
        Similarity scores as numpy array (N,)
    """
    # Normalize features
    image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    text_features = text_features / text_features.norm(dim=-1, keepdim=True)
    
    # Compute cosine similarity
    similarity = (image_features @ text_features.T).squeeze(0)
    
    return similarity.cpu().numpy()


def detect_with_openclip(
    img_array: np.ndarray,
    image_type: str
) -> Dict:
    """
    Detect AI-generated artwork using OpenCLIP semantic analysis.
    
    Args:
        img_array: RGB image as numpy array (H, W, 3)
        image_type: Image type from classifier
    
    Returns:
        Dict with:
            - ai_art_probability: float (0-1)
            - real_photo_probability: float (0-1)
            - generator: str (most likely AI generator)
            - generator_confidence: float (0-1)
            - semantic_scores: dict (individual prompt scores)
    """
    # Check if OpenCLIP is available
    model, preprocess, device = _get_model()
    
    if model is None:
        print("[OPENCLIP] Model not available, returning neutral scores")
        return {
            "ai_art_probability": 0.5,
            "real_photo_probability": 0.5,
            "generator": "unknown",
            "generator_confidence": 0.0,
            "semantic_scores": {}
        }
    
    try:
        # Preprocess image
        from PIL import Image
        pil_image = Image.fromarray(img_array)
        image_input = preprocess(pil_image).unsqueeze(0).to(device)
        
        # Encode image
        with torch.no_grad():
            image_features = model.encode_image(image_input)
        
        # Tokenize and encode text prompts
        import open_clip
        tokenizer = open_clip.get_tokenizer(model.config['vision_cfg']['model'])
        
        # Combine all prompts
        all_prompts = REAL_PHOTO_PROMPTS + AI_GENERATOR_PROMPTS
        text_tokens = tokenizer(all_prompts).to(device)
        
        with torch.no_grad():
            text_features = model.encode_text(text_tokens)
        
        # Compute cosine similarity for all prompts
        similarity_scores = _compute_cosine_similarity(image_features, text_features)
        
        # Split scores
        real_photo_scores = similarity_scores[:len(REAL_PHOTO_PROMPTS)]
        ai_generator_scores = similarity_scores[len(REAL_PHOTO_PROMPTS):]
        
        # Calculate probabilities using softmax
        real_photo_softmax = torch.softmax(torch.tensor(real_photo_scores), dim=0).numpy()
        ai_generator_softmax = torch.softmax(torch.tensor(ai_generator_scores), dim=0).numpy()
        
        # Aggregate probabilities
        real_photo_probability = float(np.mean(real_photo_softmax))
        ai_art_probability = float(np.mean(ai_generator_softmax))
        
        # Normalize to sum to 1
        total = real_photo_probability + ai_art_probability
        if total > 0:
            real_photo_probability /= total
            ai_art_probability /= total
        
        # Identify most likely AI generator
        generator_idx = int(np.argmax(ai_generator_scores))
        generator = AI_GENERATOR_PROMPTS[generator_idx]
        generator_confidence = float(ai_generator_softmax[generator_idx])
        
        # Build semantic scores dictionary
        semantic_scores = {}
        for i, prompt in enumerate(REAL_PHOTO_PROMPTS):
            semantic_scores[f"real_{i}"] = float(real_photo_scores[i])
        for i, prompt in enumerate(AI_GENERATOR_PROMPTS):
            semantic_scores[f"ai_{i}"] = float(ai_generator_scores[i])
        
        print(f"[OPENCLIP] ai_prob={ai_art_probability:.3f}, real_prob={real_photo_probability:.3f}")
        print(f"[OPENCLIP] generator={generator}, confidence={generator_confidence:.3f}")
        
        return {
            "ai_art_probability": ai_art_probability,
            "real_photo_probability": real_photo_probability,
            "generator": generator,
            "generator_confidence": generator_confidence,
            "semantic_scores": semantic_scores
        }
        
    except Exception as e:
        print(f"[OPENCLIP] Detection failed: {e}")
        return {
            "ai_art_probability": 0.5,
            "real_photo_probability": 0.5,
            "generator": "unknown",
            "generator_confidence": 0.0,
            "semantic_scores": {}
        }


def should_use_openclip(image_type: str) -> bool:
    """
    Determine if OpenCLIP should be used for this image type.
    
    Args:
        image_type: Image type from classifier
    
    Returns:
        True if OpenCLIP should be used
    """
    return image_type in ["artwork", "cartoon", "ai_artwork", "mixed_scene"]

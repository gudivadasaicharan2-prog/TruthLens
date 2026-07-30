# TruthLens Fusion Configuration
# This file controls the weighted fusion of different AI detection modules

class FusionConfig:
    """Configuration for fusion weights and thresholds."""
    
    # Decision threshold for AI classification (0.0 to 1.0)
    # Lower threshold = more sensitive to AI detection
    DECISION_THRESHOLD = 0.35
    
    # Fusion weights for different image types
    # These weights determine how much each module contributes to the final decision
    
    # Document pipeline (forensic-heavy) - v2.2 adaptive
    DOCUMENT_PIPELINE = {
        'whole_image': 0.00,
        'face': 0.00,
        'forensic': 1.00,
        'clip': 0.00,
        'patch': 0.00,
        'ood': 0.00
    }
    
    # Artwork pipeline (frequency + texture + CLIP + noise) - v2.2 adaptive
    ARTWORK_PIPELINE = {
        'whole_image': 0.00,
        'face': 0.00,
        'forensic': 1.00,
        'clip': 0.00,
        'patch': 0.00,
        'ood': 0.00
    }
    
    # Landscape/object pipeline (EfficientNet + frequency + texture) - v2.2 adaptive
    LANDSCAPE_PIPELINE = {
        'whole_image': 0.50,
        'face': 0.00,
        'forensic': 0.50,
        'clip': 0.00,
        'patch': 0.00,
        'ood': 0.00
    }
    
    # Portrait pipeline (face + EfficientNet + frequency + texture) - v2.2 adaptive
    PORTRAIT_PIPELINE = {
        'whole_image': 0.30,
        'face': 0.45,
        'forensic': 0.25,
        'clip': 0.00,
        'patch': 0.00,
        'ood': 0.00
    }
    
    # Default pipeline with faces
    DEFAULT_WITH_FACES = {
        'whole_image': 0.55,
        'face': 0.30,
        'forensic': 0.15
    }
    
    # Default pipeline without faces
    DEFAULT_NO_FACES = {
        'whole_image': 0.75,
        'face': 0.00,
        'forensic': 0.25
    }
    
    # Forensic bundle weights (must sum to 1.0) - v2.2 enhanced
    FORENSIC_WEIGHTS = {
        'ela': 0.20,          # Error Level Analysis
        'noise': 0.18,        # Noise/splicing analysis (enhanced with wavelet)
        'frequency': 0.22,    # Frequency domain analysis (enhanced with entropy)
        'texture': 0.18,      # Texture uniformity
        'edge': 0.12,         # Edge consistency
        'color': 0.06,        # Color channel anomaly
        'exif': 0.04          # EXIF metadata consistency
    }
    
    # v2.2 Adaptive forensic weights by image type
    FORENSIC_WEIGHTS_ADAPTIVE = {
        'portrait': {
            'ela': 0.15,
            'noise': 0.15,
            'frequency': 0.20,
            'texture': 0.25,
            'edge': 0.15,
            'color': 0.05,
            'exif': 0.05
        },
        'landscape': {
            'ela': 0.20,
            'noise': 0.18,
            'frequency': 0.25,
            'texture': 0.20,
            'edge': 0.10,
            'color': 0.04,
            'exif': 0.03
        },
        'artwork': {
            'ela': 0.18,
            'noise': 0.15,
            'frequency': 0.30,
            'texture': 0.30,
            'edge': 0.04,
            'color': 0.02,
            'exif': 0.01
        },
        'document': {
            'ela': 0.25,
            'noise': 0.25,
            'frequency': 0.20,
            'texture': 0.15,
            'edge': 0.10,
            'color': 0.03,
            'exif': 0.02
        },
        'default': {
            'ela': 0.20,
            'noise': 0.18,
            'frequency': 0.22,
            'texture': 0.18,
            'edge': 0.12,
            'color': 0.06,
            'exif': 0.04
        }
    }
    
    # Verdict thresholds (0.0 to 1.0)
    VERDICT_THRESHOLDS = {
        'deepfake': 0.82,
        'ai_generated': 0.68,
        'suspicious': 0.50,
        'likely_authentic': 0.30,
        'authentic': 0.00
    }
    
    # Confidence calibration parameters
    CONFIDENCE_CALIBRATION = {
        'scale': 12.0,        # Logistic scale factor
        'min_confidence': 0.50,
        'max_confidence': 0.99
    }
    
    # v2.2 Temperature scaling parameters
    # Temperature scaling calibrates confidence without retraining
    # T > 1: Softens predictions (more uncertain)
    # T < 1: Sharpens predictions (more confident)
    # T = 1: No scaling (original predictions)
    TEMPERATURE_SCALING = {
        'temperature': 1.0,  # Default temperature (no scaling)
        'enable_temperature': False,  # Enable/disable temperature scaling
        'adaptive_temperature': True,  # Adapt temperature based on OOD score
        'min_temperature': 0.8,  # Minimum temperature for adaptive scaling
        'max_temperature': 2.0  # Maximum temperature for adaptive scaling
    }
    
    # AI probability display multipliers (for frontend display)
    AI_PROBABILITY_MULTIPLIERS = {
        'deepfake': {
            'ai': 60.0,
            'deepfake': 115.0
        },
        'ai_generated': {
            'ai': 118.0,
            'deepfake': 18.0
        },
        'suspicious': {
            'ai': 75.0,
            'deepfake': 55.0
        },
        'likely_authentic': {
            'ai': 28.0,
            'deepfake': 18.0
        },
        'authentic': {
            'ai': 14.0,
            'deepfake': 9.0
        }
    }
    
    @classmethod
    def get_pipeline_weights(cls, pipeline: str, image_type: str = None) -> dict:
        """Get fusion weights for a specific pipeline."""
        pipeline_map = {
            'document': cls.DOCUMENT_PIPELINE,
            'artwork': cls.ARTWORK_PIPELINE,
            'landscape': cls.LANDSCAPE_PIPELINE,
            'portrait': cls.PORTRAIT_PIPELINE,
            'whole_image': cls.DEFAULT_NO_FACES,
            'face': cls.DEFAULT_WITH_FACES
        }
        
        # Fallback based on image type
        if pipeline not in pipeline_map and image_type:
            if image_type in ['artwork', 'cartoon', 'ai_artwork']:
                return cls.ARTWORK_PIPELINE
            elif image_type in ['landscape', 'object', 'mixed_scene']:
                return cls.LANDSCAPE_PIPELINE
            elif image_type in ['portrait', 'selfie']:
                return cls.PORTRAIT_PIPELINE
        
        return pipeline_map.get(pipeline, cls.DEFAULT_NO_FACES)
    
    @classmethod
    def get_adaptive_forensic_weights(cls, image_type: str = None) -> dict:
        """
        Get adaptive forensic weights based on image type.
        
        v2.2: Dynamically adjusts forensic module weights based on image type
        for more accurate detection across different content types.
        
        Args:
            image_type: Type of image (portrait, landscape, artwork, document, etc.)
            
        Returns:
            Dictionary of forensic module weights
        """
        if image_type and image_type in cls.FORENSIC_WEIGHTS_ADAPTIVE:
            return cls.FORENSIC_WEIGHTS_ADAPTIVE[image_type]
        
        return cls.FORENSIC_WEIGHTS_ADAPTIVE['default']
    
    @classmethod
    def get_adaptive_pipeline_weights(cls, image_type: str, has_faces: bool = False) -> dict:
        """
        Get fully adaptive pipeline weights based on image type and face detection.
        
        v2.2: Implements the adaptive fusion strategy:
        - Portrait: Face 45%, EfficientNet 30%, Frequency 15%, Texture 10%
        - Landscape: EfficientNet 50%, Frequency 30%, Texture 20%
        - Artwork: Frequency 35%, Texture 35%, CLIP 20%, Noise 10%
        - Document: Frequency 40%, Noise 30%, Texture 20%, Metadata 10%
        
        Args:
            image_type: Type of image (portrait, landscape, artwork, document, etc.)
            has_faces: Whether faces were detected in the image
            
        Returns:
            Dictionary of pipeline weights
        """
        # Map image types to adaptive weights
        if image_type in ['portrait', 'selfie', 'face_photo']:
            # Portrait: Face-heavy with forensic support
            return {
                'whole_image': 0.30,
                'face': 0.45,
                'forensic': 0.25,
                'clip': 0.00,
                'patch': 0.00,
                'ood': 0.00
            }
        elif image_type in ['landscape', 'object', 'mixed_scene']:
            # Landscape: EfficientNet + forensic
            return {
                'whole_image': 0.50,
                'face': 0.00,
                'forensic': 0.50,
                'clip': 0.00,
                'patch': 0.00,
                'ood': 0.00
            }
        elif image_type in ['artwork', 'cartoon', 'ai_artwork', 'graphic']:
            # Artwork: Forensic-heavy (frequency + texture)
            return {
                'whole_image': 0.00,
                'face': 0.00,
                'forensic': 1.00,
                'clip': 0.00,
                'patch': 0.00,
                'ood': 0.00
            }
        elif image_type in ['document', 'screenshot', 'text']:
            # Document: Forensic-heavy
            return {
                'whole_image': 0.00,
                'face': 0.00,
                'forensic': 1.00,
                'clip': 0.00,
                'patch': 0.00,
                'ood': 0.00
            }
        else:
            # Default: Balanced approach
            if has_faces:
                return cls.DEFAULT_WITH_FACES
            else:
                return cls.DEFAULT_NO_FACES

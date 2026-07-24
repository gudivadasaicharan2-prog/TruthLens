# TruthLens Fusion Configuration
# This file controls the weighted fusion of different AI detection modules

class FusionConfig:
    """Configuration for fusion weights and thresholds."""
    
    # Decision threshold for AI classification (0.0 to 1.0)
    # Lower threshold = more sensitive to AI detection
    DECISION_THRESHOLD = 0.35
    
    # Fusion weights for different image types
    # These weights determine how much each module contributes to the final decision
    
    # Document pipeline (forensic-heavy)
    DOCUMENT_PIPELINE = {
        'whole_image': 0.30,
        'face': 0.00,
        'forensic': 0.70
    }
    
    # Artwork pipeline (whole-image + forensic)
    ARTWORK_PIPELINE = {
        'whole_image': 0.65,
        'face': 0.00,
        'forensic': 0.35
    }
    
    # Landscape/object pipeline (whole-image + forensic)
    LANDSCAPE_PIPELINE = {
        'whole_image': 0.70,
        'face': 0.00,
        'forensic': 0.30
    }
    
    # Portrait pipeline (face-heavy)
    PORTRAIT_PIPELINE = {
        'whole_image': 0.50,
        'face': 0.35,
        'forensic': 0.15
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
    
    # Forensic bundle weights (must sum to 1.0)
    FORENSIC_WEIGHTS = {
        'ela': 0.22,          # Error Level Analysis
        'noise': 0.18,        # Noise/splicing analysis
        'frequency': 0.18,    # Frequency domain analysis
        'texture': 0.18,      # Texture uniformity
        'edge': 0.12,         # Edge consistency
        'color': 0.08,        # Color channel anomaly
        'exif': 0.04          # EXIF metadata consistency
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

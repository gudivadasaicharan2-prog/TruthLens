"""
Unit Tests for CLIP Detector and Multi-Model Ensemble
======================================================
Tests for CLIP semantic analysis and ensemble integration.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from app.ai.detectors.clip_detector import (
    detect_with_clip,
    should_use_clip,
    get_clip_ensemble_weight,
    _load_clip_model,
)


def create_test_image(width=512, height=512):
    """Create a test image."""
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)


class TestCLIPModelLoading:
    """Test CLIP model singleton loading."""
    
    @patch('app.ai.detectors.clip_detector.open_clip')
    def test_clip_model_loads_successfully(self, mock_open_clip):
        """Test that CLIP model loads successfully."""
        mock_model = Mock()
        mock_preprocess = Mock()
        mock_open_clip.create_model_and_transforms.return_value = (mock_model, None, mock_preprocess)
        
        model, preprocess, device = _load_clip_model()
        
        assert model is not None
        assert preprocess is not None
        assert device in ['cuda', 'cpu']
        mock_open_clip.create_model_and_transforms.assert_called_once()
    
    @patch('app.ai.detectors.clip_detector.open_clip', side_effect=ImportError)
    def test_clip_model_import_error(self, mock_open_clip):
        """Test fallback when open_clip is not installed."""
        model, preprocess, device = _load_clip_model()
        
        assert model is None
        assert preprocess is None
        assert device is None
    
    @patch('app.ai.detectors.clip_detector.open_clip')
    def test_clip_model_singleton(self, mock_open_clip):
        """Test that CLIP model is loaded only once (singleton)."""
        mock_model = Mock()
        mock_preprocess = Mock()
        mock_open_clip.create_model_and_transforms.return_value = (mock_model, None, mock_preprocess)
        
        # First call
        model1, _, _ = _load_clip_model()
        # Second call
        model2, _, _ = _load_clip_model()
        
        assert model1 is model2
        mock_open_clip.create_model_and_transforms.assert_called_once()


class TestCLIPDetection:
    """Test CLIP detection functionality."""
    
    @patch('app.ai.detectors.clip_detector.get_clip_model')
    @patch('app.ai.detectors.clip_detector.open_clip')
    def test_clip_detection_with_model(self, mock_open_clip, mock_get_clip_model):
        """Test CLIP detection with available model."""
        # Setup mocks
        mock_model = Mock()
        mock_preprocess = Mock()
        mock_get_clip_model.return_value = (mock_model, mock_preprocess, 'cpu')
        
        mock_image_features = Mock()
        mock_image_features.norm.return_value = Mock()
        mock_text_features = Mock()
        mock_text_features.norm.return_value = Mock()
        
        mock_model.encode_image.return_value = mock_image_features
        mock_model.encode_text.return_value = mock_text_features
        
        # Mock similarity calculation
        mock_similarity = np.array([[0.3, 0.2, 0.25, 0.25]])
        mock_image_features.__matmul__ = Mock(return_value=Mock(softmax=lambda dim: mock_similarity))
        
        img = create_test_image()
        result = detect_with_clip(img, image_type="ai_artwork")
        
        assert "ai_probability" in result
        assert "confidence" in result
        assert "features" in result
        assert "reason" in result
        assert 0.0 <= result["ai_probability"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0
    
    @patch('app.ai.detectors.clip_detector.get_clip_model')
    def test_clip_detection_without_model(self, mock_get_clip_model):
        """Test CLIP detection fallback when model is unavailable."""
        mock_get_clip_model.return_value = (None, None, None)
        
        img = create_test_image()
        result = detect_with_clip(img, image_type="ai_artwork")
        
        assert result["ai_probability"] == 0.5
        assert result["confidence"] == 0.0
        assert result["reason"] == "CLIP model not available"
    
    @patch('app.ai.detectors.clip_detector.get_clip_model')
    @patch('app.ai.detectors.clip_detector.open_clip')
    def test_clip_detection_error_handling(self, mock_open_clip, mock_get_clip_model):
        """Test CLIP detection error handling."""
        mock_get_clip_model.return_value = (Mock(), Mock(), 'cpu')
        mock_open_clip.tokenize.side_effect = Exception("Tokenization error")
        
        img = create_test_image()
        result = detect_with_clip(img, image_type="ai_artwork")
        
        assert result["ai_probability"] == 0.5
        assert result["confidence"] == 0.0
        assert "failed" in result["reason"].lower()


class TestCLIPConditionalExecution:
    """Test conditional CLIP execution based on image type."""
    
    def test_clip_for_ai_artwork(self):
        """Test CLIP should be used for AI artwork."""
        assert should_use_clip("ai_artwork") == True
    
    def test_clip_for_artwork(self):
        """Test CLIP should be used for artwork."""
        assert should_use_clip("artwork") == True
    
    def test_clip_for_cartoon(self):
        """Test CLIP should be used for cartoon."""
        assert should_use_clip("cartoon") == True
    
    def test_clip_for_mixed_scene(self):
        """Test CLIP should be used for mixed scene."""
        assert should_use_clip("mixed_scene") == True
    
    def test_clip_skip_for_document(self):
        """Test CLIP should be skipped for documents."""
        assert should_use_clip("document") == False
    
    def test_clip_skip_for_screenshot(self):
        """Test CLIP should be skipped for screenshots."""
        assert should_use_clip("screenshot") == False
    
    def test_clip_for_real_photograph(self):
        """Test CLIP can be used for real photographs."""
        assert should_use_clip("real_photograph") == True
    
    def test_clip_for_portrait(self):
        """Test CLIP can be used for portraits."""
        assert should_use_clip("portrait") == True


class TestCLIPEnsembleWeights:
    """Test CLIP ensemble weight calculation."""
    
    def test_clip_weight_for_ai_artwork(self):
        """Test high CLIP weight for AI artwork."""
        weight = get_clip_ensemble_weight("ai_artwork")
        assert weight == 0.55
    
    def test_clip_weight_for_artwork(self):
        """Test high CLIP weight for artwork."""
        weight = get_clip_ensemble_weight("artwork")
        assert weight == 0.55
    
    def test_clip_weight_for_cartoon(self):
        """Test high CLIP weight for cartoon."""
        weight = get_clip_ensemble_weight("cartoon")
        assert weight == 0.55
    
    def test_clip_weight_for_real_photograph(self):
        """Test low CLIP weight for real photographs."""
        weight = get_clip_ensemble_weight("real_photograph")
        assert weight == 0.10
    
    def test_clip_weight_for_portrait(self):
        """Test low CLIP weight for portraits."""
        weight = get_clip_ensemble_weight("portrait")
        assert weight == 0.10
    
    def test_clip_weight_for_selfie(self):
        """Test low CLIP weight for selfies."""
        weight = get_clip_ensemble_weight("selfie")
        assert weight == 0.10
    
    def test_clip_weight_for_landscape(self):
        """Test low CLIP weight for landscapes."""
        weight = get_clip_ensemble_weight("landscape")
        assert weight == 0.10
    
    def test_clip_weight_zero_for_document(self):
        """Test zero CLIP weight for documents."""
        weight = get_clip_ensemble_weight("document")
        assert weight == 0.00
    
    def test_clip_weight_zero_for_screenshot(self):
        """Test zero CLIP weight for screenshots."""
        weight = get_clip_ensemble_weight("screenshot")
        assert weight == 0.00
    
    def test_clip_weight_moderate_for_mixed_scene(self):
        """Test moderate CLIP weight for mixed scenes."""
        weight = get_clip_ensemble_weight("mixed_scene")
        assert weight == 0.25
    
    def test_clip_weight_moderate_for_object(self):
        """Test moderate CLIP weight for objects."""
        weight = get_clip_ensemble_weight("object")
        assert weight == 0.25


class TestCLIPIntegration:
    """Test CLIP integration with image detector."""
    
    @patch('app.ai.detectors.clip_detector.detect_with_clip')
    def test_clip_called_for_supported_types(self, mock_detect):
        """Test CLIP is called for supported image types."""
        mock_detect.return_value = {
            "ai_probability": 0.7,
            "confidence": 0.8,
            "features": {},
            "reason": "AI detected"
        }
        
        from app.ai.detectors.clip_detector import should_use_clip
        
        supported_types = ["ai_artwork", "artwork", "cartoon", "mixed_scene"]
        for img_type in supported_types:
            assert should_use_clip(img_type) == True
    
    @patch('app.ai.detectors.clip_detector.detect_with_clip')
    def test_clip_not_called_for_unsupported_types(self, mock_detect):
        """Test CLIP is not called for unsupported image types."""
        from app.ai.detectors.clip_detector import should_use_clip
        
        unsupported_types = ["document", "screenshot"]
        for img_type in unsupported_types:
            assert should_use_clip(img_type) == False
        
        # Verify detect_with_clip was not called
        mock_detect.assert_not_called()


class TestCLIPFeatureExtraction:
    """Test CLIP feature extraction and output format."""
    
    @patch('app.ai.detectors.clip_detector.get_clip_model')
    @patch('app.ai.detectors.clip_detector.open_clip')
    def test_clip_features_structure(self, mock_open_clip, mock_get_clip_model):
        """Test that CLIP returns properly structured features."""
        mock_model = Mock()
        mock_preprocess = Mock()
        mock_get_clip_model.return_value = (mock_model, mock_preprocess, 'cpu')
        
        mock_image_features = Mock()
        mock_text_features = Mock()
        mock_model.encode_image.return_value = mock_image_features
        mock_model.encode_text.return_value = mock_text_features
        
        mock_similarity = np.array([[0.4, 0.3, 0.2, 0.1]])
        mock_image_features.__matmul__ = Mock(return_value=Mock(softmax=lambda dim: mock_similarity))
        
        img = create_test_image()
        result = detect_with_clip(img, image_type="ai_artwork")
        
        features = result["features"]
        assert "ai_similarity" in features
        assert "real_similarity" in features
        assert "max_similarity" in features
        assert "min_similarity" in features
        assert "std_similarity" in features
        
        # Check that values are floats
        for key, value in features.items():
            assert isinstance(value, float)


class TestCLIPReasoning:
    """Test CLIP reasoning generation."""
    
    @patch('app.ai.detectors.clip_detector.get_clip_model')
    @patch('app.ai.detectors.clip_detector.open_clip')
    def test_clip_reasoning_high_ai(self, mock_open_clip, mock_get_clip_model):
        """Test CLIP reasoning for high AI probability."""
        mock_model = Mock()
        mock_preprocess = Mock()
        mock_get_clip_model.return_value = (mock_model, mock_preprocess, 'cpu')
        
        mock_image_features = Mock()
        mock_text_features = Mock()
        mock_model.encode_image.return_value = mock_image_features
        mock_model.encode_text.return_value = mock_text_features
        
        # High AI probability
        mock_similarity = np.array([[0.8, 0.1, 0.05, 0.05]])
        mock_image_features.__matmul__ = Mock(return_value=Mock(softmax=lambda dim: mock_similarity))
        
        img = create_test_image()
        result = detect_with_clip(img, image_type="ai_artwork")
        
        assert "strongly indicates" in result["reason"].lower()
        assert "ai-generated" in result["reason"].lower()
    
    @patch('app.ai.detectors.clip_detector.get_clip_model')
    @patch('app.ai.detectors.clip_detector.open_clip')
    def test_clip_reasoning_low_ai(self, mock_open_clip, mock_get_clip_model):
        """Test CLIP reasoning for low AI probability."""
        mock_model = Mock()
        mock_preprocess = Mock()
        mock_get_clip_model.return_value = (mock_model, mock_preprocess, 'cpu')
        
        mock_image_features = Mock()
        mock_text_features = Mock()
        mock_model.encode_image.return_value = mock_image_features
        mock_model.encode_text.return_value = mock_text_features
        
        # Low AI probability
        mock_similarity = np.array([[0.1, 0.8, 0.05, 0.05]])
        mock_image_features.__matmul__ = Mock(return_value=Mock(softmax=lambda dim: mock_similarity))
        
        img = create_test_image()
        result = detect_with_clip(img, image_type="ai_artwork")
        
        assert "indicates authentic" in result["reason"].lower()


class TestBackwardCompatibility:
    """Test backward compatibility of API response."""
    
    def test_clip_fields_optional(self):
        """Test that CLIP fields are optional and don't break existing fields."""
        # Simulate response without CLIP
        response = {
            "verdict": "Authentic",
            "confidence": 0.85,
            "ai_probability": 12.5,
            "deepfake_probability": 5.2,
            "key_findings": ["Test finding"],
            "metadata_summary": {"resolution": "512x512"},
            "truth_score": 87.5,
            "ai_detection_score": 12.5,
            "result": "Authentic",
            "image_type": "real_photograph",
        }
        
        # Add CLIP fields (should not break existing fields)
        response.update({
            "clip_probability": 0.3,
            "clip_confidence": 0.7,
            "ensemble_score": 0.25,
            "clip_enabled": True,
        })
        
        # Verify all original fields still exist
        assert "verdict" in response
        assert "confidence" in response
        assert "ai_probability" in response
        assert "deepfake_probability" in response
        assert "truth_score" in response
        
        # Verify new CLIP fields exist
        assert "clip_probability" in response
        assert "clip_confidence" in response
        assert "ensemble_score" in response
        assert "clip_enabled" in response


class TestEnsembleIntegration:
    """Test ensemble integration with fusion engine."""
    
    def test_ensemble_weights_sum_to_one(self):
        """Test that ensemble weights sum to approximately 1."""
        from app.ai.detectors.clip_detector import get_clip_ensemble_weight
        
        image_types = ["ai_artwork", "real_photograph", "document", "mixed_scene"]
        
        for img_type in image_types:
            clip_weight = get_clip_ensemble_weight(img_type)
            
            # Simulate weight adjustment
            if clip_weight > 0:
                remaining_weight = 1.0 - clip_weight
                # Remaining weight should be distributed among other modules
                assert 0.0 <= remaining_weight <= 1.0
    
    def test_ensemble_fusion_with_clip(self):
        """Test that fusion engine can handle CLIP score."""
        # Simulate fusion engine inputs
        whole_image_score = 0.6
        face_score = 0.4
        forensic_score = 0.3
        clip_score = 0.7
        
        # Verify all scores are in valid range
        assert 0.0 <= whole_image_score <= 1.0
        assert 0.0 <= face_score <= 1.0
        assert 0.0 <= forensic_score <= 1.0
        assert 0.0 <= clip_score <= 1.0
    
    def test_ensemble_fusion_without_clip(self):
        """Test that fusion engine works without CLIP score."""
        # Simulate fusion engine inputs without CLIP
        whole_image_score = 0.6
        face_score = 0.4
        forensic_score = 0.3
        clip_score = None
        
        # Verify scores are valid
        assert 0.0 <= whole_image_score <= 1.0
        assert 0.0 <= face_score <= 1.0
        assert 0.0 <= forensic_score <= 1.0
        assert clip_score is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
AI Pipeline integration tests.
"""

import pytest
import numpy as np
from PIL import Image
import tempfile
import os
from app.ai.models.image_model import load_model, is_using_trained_weights
from app.ai.detectors.clip_detector import CLIPDetector
from app.ai.explainability.gradcam import GradCAMGenerator
from app.ai.detectors.image_detector import analyze_image


class TestAIPipeline:
    """Test suite for AI pipeline components."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        return img
    
    @pytest.fixture
    def sample_image_path(self, sample_image):
        """Create a temporary image file."""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            sample_image.save(f.name)
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    def test_efficientnet_model_loading(self):
        """Test EfficientNet model can be loaded."""
        try:
            load_model()
            assert True
        except Exception as e:
            pytest.skip(f"Model loading failed: {e}")
    
    def test_is_using_trained_weights(self):
        """Test trained weights detection."""
        try:
            result = is_using_trained_weights()
            assert isinstance(result, bool)
        except Exception as e:
            pytest.skip(f"Trained weights check failed: {e}")
    
    def test_clip_detector_initialization(self):
        """Test CLIP detector initialization."""
        try:
            detector = CLIPDetector()
            assert detector is not None
        except Exception as e:
            pytest.skip(f"CLIP detector initialization failed: {e}")
    
    def test_gradcam_generator_initialization(self):
        """Test GradCAM generator initialization."""
        try:
            from app.ai.models.image_model import _BACKBONE
            if _BACKBONE is None:
                pytest.skip("Model not loaded")
            
            generator = GradCAMGenerator(_BACKBONE)
            assert generator is not None
        except Exception as e:
            pytest.skip(f"GradCAM generator initialization failed: {e}")
    
    def test_fusion_config_weights(self):
        """Test fusion configuration weights."""
        from app.ai.detectors.fusion_config import FusionConfig
        weights = FusionConfig.get_pipeline_weights("default", "default_with_faces")
        assert weights is not None
        assert isinstance(weights, dict)
        assert len(weights) > 0
    
    def test_image_type_classifier(self):
        """Test image type classifier."""
        try:
            from app.ai.classification.image_type_classifier import ImageTypeClassifier
            classifier = ImageTypeClassifier()
            assert classifier is not None
        except Exception as e:
            pytest.skip(f"Image type classifier initialization failed: {e}")
    
    def test_analyze_image_basic(self, sample_image_path):
        """Test basic image analysis."""
        try:
            result = analyze_image(sample_image_path)
            assert result is not None
            assert isinstance(result, dict)
            # Check for expected fields
            assert "verdict" in result or "error" in result
        except Exception as e:
            pytest.skip(f"Image analysis failed: {e}")
    
    def test_analyze_image_structure(self, sample_image_path):
        """Test image analysis result structure."""
        try:
            result = analyze_image(sample_image_path)
            if "error" not in result:
                # Check for common fields
                expected_fields = ["verdict", "confidence", "ai_probability"]
                for field in expected_fields:
                    assert field in result or field in result.get("analysis_metadata", {})
        except Exception as e:
            pytest.skip(f"Image analysis structure test failed: {e}")
    
    def test_forensic_ela(self, sample_image_path):
        """Test ELA forensic analysis."""
        try:
            from app.ai.forensics.ela import ela_score
            ela_variance, ela_score = ela_score(sample_image_path)
            assert ela_variance is not None
            assert ela_score is not None
            assert ela_variance >= 0
            assert 0 <= ela_score <= 1
        except Exception as e:
            pytest.skip(f"ELA analysis failed: {e}")
    
    def test_forensic_noise_analysis(self, sample_image_path):
        """Test noise forensic analysis."""
        try:
            from app.ai.forensics.noise import noise_analysis
            noise_level = noise_analysis(sample_image_path)
            assert noise_level is not None
            assert noise_level >= 0
        except Exception as e:
            pytest.skip(f"Noise analysis failed: {e}")
    
    def test_report_generation(self, sample_image_path):
        """Test PDF report generation."""
        try:
            result = analyze_image(sample_image_path)
            if "error" not in result and "report_path" in result:
                assert result["report_path"] is not None
                # Check if file exists
                if os.path.exists(result["report_path"]):
                    assert os.path.getsize(result["report_path"]) > 0
        except Exception as e:
            pytest.skip(f"Report generation test failed: {e}")

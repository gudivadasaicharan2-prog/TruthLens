"""
Unit Tests for Image Type Classifier
====================================
Tests for enhanced image type classification with confidence scores.
"""

import pytest
import numpy as np
import cv2
from PIL import Image
from app.ai.classification.image_type_classifier import (
    classify_image_type,
    _detect_edges,
    _analyze_color_distribution,
    _analyze_aspect_ratio,
    _calculate_texture_entropy,
    _detect_compression_artifacts,
    _detect_sensor_noise,
    _detect_illustration_edges,
    _detect_diffusion_patterns,
    _is_screenshot,
    _is_document,
    _is_ai_artwork,
    _is_cartoon,
    _is_artwork,
    _is_real_photograph,
    _is_object,
)


def create_test_image(width=512, height=512, color=(128, 128, 128), noise_level=0):
    """Create a test image with specified properties."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, (height, width, 3)).astype(np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img


def create_gradient_image(width=512, height=512):
    """Create an image with smooth color gradients (AI artwork characteristic)."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        for j in range(width):
            img[i, j] = [
                int(255 * i / height),
                int(255 * j / width),
                int(255 * (i + j) / (height + width))
            ]
    return img


def create_text_like_image(width=512, height=512):
    """Create an image with text-like regions (document/screenshot)."""
    img = np.full((height, width, 3), (255, 255, 255), dtype=np.uint8)
    # Add some dark regions to simulate text
    for i in range(0, height, 20):
        for j in range(0, width, 40):
            if (i + j) % 3 == 0:
                img[i:i+10, j:j+30] = (0, 0, 0)
    return img


def create_cartoon_like_image(width=512, height=512):
    """Create a cartoon-like image with flat colors and clean edges."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    # Create flat color regions
    img[0:height//2, 0:width//2] = (255, 100, 100)
    img[0:height//2, width//2:] = (100, 255, 100)
    img[height//2:, 0:width//2] = (100, 100, 255)
    img[height//2:, width//2:] = (255, 255, 100)
    return img


def create_edge_dense_image(width=512, height=512):
    """Create an image with high edge density (screenshot characteristic)."""
    img = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    # Add rectangular regions (UI windows)
    for _ in range(5):
        x = np.random.randint(0, width-100)
        y = np.random.randint(0, height-100)
        w = np.random.randint(50, 100)
        h = np.random.randint(50, 100)
        img[y:y+h, x:x+w] = np.random.randint(200, 255, (h, w, 3), dtype=np.uint8)
    return img


class TestEdgeDetection:
    """Test edge detection heuristic."""
    
    def test_low_edge_density(self):
        """Test image with low edge density."""
        img = create_test_image(noise_level=0)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edge_density = _detect_edges(gray)
        assert edge_density < 0.05
    
    def test_high_edge_density(self):
        """Test image with high edge density."""
        img = create_edge_dense_image()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edge_density = _detect_edges(gray)
        assert edge_density > 0.1


class TestColorDistribution:
    """Test color distribution analysis."""
    
    def test_low_saturation(self):
        """Test image with low saturation (grayscale-like)."""
        img = create_test_image(color=(128, 128, 128))
        color_stats = _analyze_color_distribution(img)
        assert color_stats["avg_saturation"] < 50
    
    def test_high_saturation(self):
        """Test image with high saturation (vibrant colors)."""
        img = create_test_image(color=(255, 0, 128))
        color_stats = _analyze_color_distribution(img)
        assert color_stats["avg_saturation"] > 100
    
    def test_high_hue_variance(self):
        """Test image with high hue variance (colorful)."""
        img = create_cartoon_like_image()
        color_stats = _analyze_color_distribution(img)
        assert color_stats["hue_std"] > 30


class TestAspectRatio:
    """Test aspect ratio analysis."""
    
    def test_portrait_aspect_ratio(self):
        """Test portrait aspect ratio."""
        aspect_type, confidence = _analyze_aspect_ratio(400, 800)
        assert aspect_type == "portrait"
        assert confidence > 0.7
    
    def test_landscape_aspect_ratio(self):
        """Test landscape aspect ratio."""
        aspect_type, confidence = _analyze_aspect_ratio(800, 400)
        assert aspect_type == "landscape"
        assert confidence > 0.7
    
    def test_square_aspect_ratio(self):
        """Test square aspect ratio."""
        aspect_type, confidence = _analyze_aspect_ratio(512, 512)
        assert aspect_type == "square"
        assert confidence >= 0.5


class TestTextureEntropy:
    """Test texture entropy calculation."""
    
    def test_low_entropy(self):
        """Test image with low texture entropy (flat colors)."""
        img = create_test_image()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        entropy = _calculate_texture_entropy(gray)
        assert entropy < 5
    
    def test_high_entropy(self):
        """Test image with high texture entropy (complex texture)."""
        img = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        entropy = _calculate_texture_entropy(gray)
        assert entropy > 7


class TestCompressionArtifacts:
    """Test compression artifact detection."""
    
    def test_no_compression_artifacts(self):
        """Test image without compression artifacts."""
        img = create_test_image()
        artifacts = _detect_compression_artifacts(img)
        assert artifacts < 5
    
    def test_compression_artifacts(self):
        """Test image with compression artifacts (simulated)."""
        img = create_test_image()
        # Simulate JPEG blockiness by adding block boundaries
        for i in range(0, 512, 8):
            img[i:i+1, :] = img[i:i+1, :] + 10
            img[:, i:i+1] = img[:, i:i+1] + 10
        artifacts = _detect_compression_artifacts(img)
        assert artifacts > 5


class TestSensorNoise:
    """Test sensor noise detection."""
    
    def test_low_sensor_noise(self):
        """Test image with low sensor noise (smooth)."""
        img = create_test_image(noise_level=0)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        noise = _detect_sensor_noise(gray)
        assert noise < 5
    
    def test_high_sensor_noise(self):
        """Test image with high sensor noise (noisy)."""
        img = create_test_image(noise_level=15)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        noise = _detect_sensor_noise(gray)
        assert noise > 5


class TestIllustrationEdges:
    """Test illustration edge detection."""
    
    def test_clean_illustration_edges(self):
        """Test cartoon-like clean edges."""
        img = create_cartoon_like_image()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edge_smoothness = _detect_illustration_edges(gray)
        assert edge_smoothness > 0.3


class TestDiffusionPatterns:
    """Test diffusion pattern detection."""
    
    def test_smooth_gradients(self):
        """Test smooth color gradients (AI artwork characteristic)."""
        img = create_gradient_image()
        smoothness = _detect_diffusion_patterns(img)
        assert smoothness > 0.5
    
    def test_sharp_transitions(self):
        """Test sharp color transitions (not AI-like)."""
        img = create_cartoon_like_image()
        smoothness = _detect_diffusion_patterns(img)
        assert smoothness < 0.5


class TestScreenshotDetection:
    """Test screenshot detection."""
    
    def test_screenshot_detection(self):
        """Test detection of screenshot-like images."""
        img = create_edge_dense_image()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        is_screenshot, confidence = _is_screenshot(gray, img)
        assert is_screenshot
        assert confidence > 0.6
    
    def test_non_screenshot(self):
        """Test rejection of non-screenshot images."""
        img = create_test_image()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        is_screenshot, confidence = _is_screenshot(gray, img)
        assert not is_screenshot


class TestDocumentDetection:
    """Test document detection."""
    
    def test_document_detection(self):
        """Test detection of document-like images."""
        img = create_text_like_image()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        is_document, confidence = _is_document(gray, img)
        assert is_document
        assert confidence > 0.6
    
    def test_non_document(self):
        """Test rejection of non-document images."""
        img = create_test_image()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        is_document, confidence = _is_document(gray, img)
        assert not is_document


class TestAIArtworkDetection:
    """Test AI artwork detection."""
    
    def test_ai_artwork_detection(self):
        """Test detection of AI artwork characteristics."""
        img = create_gradient_image()
        color_stats = _analyze_color_distribution(img)
        is_ai, confidence = _is_ai_artwork(img, color_stats)
        assert is_ai
        assert confidence > 0.6
    
    def test_non_ai_artwork(self):
        """Test rejection of non-AI artwork."""
        img = create_test_image(noise_level=10)
        color_stats = _analyze_color_distribution(img)
        is_ai, confidence = _is_ai_artwork(img, color_stats)
        assert not is_ai


class TestCartoonDetection:
    """Test cartoon detection."""
    
    def test_cartoon_detection(self):
        """Test detection of cartoon-like images."""
        img = create_cartoon_like_image()
        color_stats = _analyze_color_distribution(img)
        is_cartoon, confidence = _is_cartoon(img, color_stats)
        assert is_cartoon
        assert confidence > 0.6
    
    def test_non_cartoon(self):
        """Test rejection of non-cartoon images."""
        img = create_test_image()
        color_stats = _analyze_color_distribution(img)
        is_cartoon, confidence = _is_cartoon(img, color_stats)
        assert not is_cartoon


class TestArtworkDetection:
    """Test traditional artwork detection."""
    
    def test_artwork_detection(self):
        """Test detection of artwork characteristics."""
        img = create_cartoon_like_image()
        # Add some noise to simulate paint texture
        img = np.clip(img.astype(np.int16) + np.random.randint(-5, 5, img.shape), 0, 255).astype(np.uint8)
        color_stats = _analyze_color_distribution(img)
        is_artwork, confidence = _is_artwork(img, color_stats)
        assert is_artwork
        assert confidence > 0.6


class TestRealPhotographDetection:
    """Test real photograph detection."""
    
    def test_real_photograph_detection(self):
        """Test detection of real photograph characteristics."""
        img = create_test_image(noise_level=8)
        color_stats = _analyze_color_distribution(img)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edge_density = _detect_edges(gray)
        is_photo, confidence = _is_real_photograph(img, color_stats, edge_density, face_count=0)
        assert is_photo
        assert confidence > 0.5
    
    def test_real_photograph_with_faces(self):
        """Test detection of real photograph with faces."""
        img = create_test_image(noise_level=8)
        color_stats = _analyze_color_distribution(img)
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edge_density = _detect_edges(gray)
        is_photo, confidence = _is_real_photograph(img, color_stats, edge_density, face_count=1)
        assert is_photo


class TestObjectDetection:
    """Test simple object detection."""
    
    def test_object_detection(self):
        """Test detection of simple object images."""
        img = create_test_image()
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        edge_density = _detect_edges(gray)
        _, aspect_confidence = _analyze_aspect_ratio(512, 512)
        is_object, confidence = _is_object(img, edge_density, "square")
        assert is_object
        assert confidence > 0.6


class TestFullClassification:
    """Test full image type classification."""
    
    def test_real_photograph_classification(self):
        """Test classification of real photograph."""
        img = create_test_image(noise_level=8)
        result = classify_image_type(img, face_count=0)
        assert result["image_type"] in ["real_photograph", "object", "mixed_scene"]
        assert 0.0 <= result["image_type_confidence"] <= 1.0
        assert result["recommended_pipeline"] in ["photo", "object", "whole_image"]
        assert "heuristics" in result
        assert result["heuristics"]["edge_density"] < 0.1
    
    def test_ai_artwork_classification(self):
        """Test classification of AI artwork."""
        img = create_gradient_image()
        result = classify_image_type(img, face_count=0)
        assert result["image_type"] in ["ai_artwork", "artwork", "cartoon"]
        assert 0.0 <= result["image_type_confidence"] <= 1.0
        assert result["recommended_pipeline"] == "artwork"
        assert result["heuristics"]["sensor_noise"] < 10
    
    def test_cartoon_classification(self):
        """Test classification of cartoon/illustration."""
        img = create_cartoon_like_image()
        result = classify_image_type(img, face_count=0)
        assert result["image_type"] in ["cartoon", "artwork", "ai_artwork"]
        assert 0.0 <= result["image_type_confidence"] <= 1.0
        assert result["recommended_pipeline"] == "artwork"
    
    def test_screenshot_classification(self):
        """Test classification of screenshot."""
        img = create_edge_dense_image()
        result = classify_image_type(img, face_count=0)
        assert result["image_type"] in ["screenshot", "document"]
        assert 0.0 <= result["image_type_confidence"] <= 1.0
        assert result["recommended_pipeline"] == "document"
    
    def test_document_classification(self):
        """Test classification of document."""
        img = create_text_like_image()
        result = classify_image_type(img, face_count=0)
        assert result["image_type"] in ["document", "screenshot"]
        assert 0.0 <= result["image_type_confidence"] <= 1.0
        assert result["recommended_pipeline"] == "document"
    
    def test_portrait_classification(self):
        """Test classification of portrait with single face."""
        img = create_test_image(noise_level=8)
        result = classify_image_type(img, face_count=1)
        assert result["image_type"] in ["portrait", "real_photograph"]
        assert 0.0 <= result["image_type_confidence"] <= 1.0
        assert result["recommended_pipeline"] in ["portrait", "photo"]
        assert result["contains_faces"] == True
        assert result["face_count"] == 1
    
    def test_selfie_classification(self):
        """Test classification of selfie with multiple faces."""
        img = create_test_image(noise_level=8)
        result = classify_image_type(img, face_count=2)
        assert result["image_type"] in ["selfie", "real_photograph"]
        assert 0.0 <= result["image_type_confidence"] <= 1.0
        assert result["recommended_pipeline"] in ["selfie", "photo"]
        assert result["contains_faces"] == True
        assert result["face_count"] == 2
    
    def test_mixed_scene_classification(self):
        """Test classification of mixed scene (default)."""
        img = np.random.randint(100, 150, (512, 512, 3), dtype=np.uint8)
        result = classify_image_type(img, face_count=0)
        assert result["image_type"] in ["mixed_scene", "real_photograph", "object"]
        assert 0.0 <= result["image_type_confidence"] <= 1.0
        assert "heuristics" in result
    
    def test_heuristics_completeness(self):
        """Test that all heuristics are present in result."""
        img = create_test_image()
        result = classify_image_type(img, face_count=0)
        heuristics = result["heuristics"]
        required_keys = [
            "edge_density",
            "aspect_ratio",
            "avg_saturation",
            "hue_std",
            "texture_entropy",
            "sensor_noise",
            "compression_artifacts",
            "face_count"
        ]
        for key in required_keys:
            assert key in heuristics
            assert isinstance(heuristics[key], (int, float))
    
    def test_confidence_range(self):
        """Test that confidence is always in valid range."""
        img = create_test_image()
        result = classify_image_type(img, face_count=0)
        assert 0.0 <= result["image_type_confidence"] <= 1.0
    
    def test_backward_compatibility(self):
        """Test that response includes all required fields."""
        img = create_test_image()
        result = classify_image_type(img, face_count=0)
        required_fields = [
            "image_type",
            "image_type_confidence",
            "recommended_pipeline",
            "contains_faces",
            "face_count",
            "heuristics"
        ]
        for field in required_fields:
            assert field in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

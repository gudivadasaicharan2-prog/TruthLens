"""
Unit tests for fusion configuration module.
"""

import pytest
from app.ai.detectors.fusion_config import FusionConfig


class TestFusionConfig:
    """Test suite for fusion configuration."""
    
    def test_fusion_config_initialization(self):
        """Test FusionConfig initialization."""
        config = FusionConfig()
        assert config is not None
        assert config.decision_threshold > 0
        assert config.decision_threshold < 1
    
    def test_get_pipeline_weights(self):
        """Test getting pipeline weights."""
        weights = FusionConfig.get_pipeline_weights("default", "default_with_faces")
        assert weights is not None
        assert isinstance(weights, dict)
    
    def test_get_pipeline_weights_document(self):
        """Test getting document pipeline weights."""
        weights = FusionConfig.get_pipeline_weights("default", "document")
        assert weights is not None
        assert isinstance(weights, dict)
    
    def test_get_pipeline_weights_artwork(self):
        """Test getting artwork pipeline weights."""
        weights = FusionConfig.get_pipeline_weights("default", "artwork")
        assert weights is not None
        assert isinstance(weights, dict)

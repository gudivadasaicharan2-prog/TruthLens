"""
Unit tests for fusion logic in image_detector.py
Tests weighted fusion, contribution tracking, and explanation generation.
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.detectors.fusion_config import FusionConfig
from app.ai.detectors.image_detector import (
    _fusion_engine,
    _generate_explanation,
    _calibrate_confidence,
)


class TestFusionConfig:
    """Test fusion configuration loading and validation."""
    
    def test_decision_threshold_exists(self):
        """Test that decision threshold is defined."""
        assert hasattr(FusionConfig, 'DECISION_THRESHOLD')
        assert 0.0 <= FusionConfig.DECISION_THRESHOLD <= 1.0
    
    def test_pipeline_weights_sum_to_one(self):
        """Test that all pipeline weights sum to approximately 1.0."""
        pipelines = [
            FusionConfig.DOCUMENT_PIPELINE,
            FusionConfig.ARTWORK_PIPELINE,
            FusionConfig.LANDSCAPE_PIPELINE,
            FusionConfig.PORTRAIT_PIPELINE,
            FusionConfig.DEFAULT_WITH_FACES,
            FusionConfig.DEFAULT_NO_FACES
        ]
        
        for pipeline in pipelines:
            total = sum(pipeline.values())
            assert abs(total - 1.0) < 0.01, f"Pipeline weights sum to {total}, expected 1.0"
    
    def test_forensic_weights_sum_to_one(self):
        """Test that forensic bundle weights sum to approximately 1.0."""
        total = sum(FusionConfig.FORENSIC_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01, f"Forensic weights sum to {total}, expected 1.0"
    
    def test_verdict_thresholds_ordered(self):
        """Test that verdict thresholds are in descending order."""
        thresholds = FusionConfig.VERDICT_THRESHOLDS
        assert thresholds['deepfake'] >= thresholds['ai_generated']
        assert thresholds['ai_generated'] >= thresholds['suspicious']
        assert thresholds['suspicious'] >= thresholds['likely_authentic']
        assert thresholds['likely_authentic'] >= thresholds['authentic']
    
    def test_get_pipeline_weights(self):
        """Test get_pipeline_weights method."""
        # Test known pipeline
        weights = FusionConfig.get_pipeline_weights('document')
        assert weights == FusionConfig.DOCUMENT_PIPELINE
        
        # Test fallback for unknown pipeline with image type
        weights = FusionConfig.get_pipeline_weights('unknown', 'artwork')
        assert weights == FusionConfig.ARTWORK_PIPELINE
        
        # Test default fallback
        weights = FusionConfig.get_pipeline_weights('unknown', 'unknown')
        assert weights == FusionConfig.DEFAULT_NO_FACES


class TestFusionEngine:
    """Test the fusion engine logic."""
    
    def test_fusion_with_faces(self):
        """Test fusion when faces are detected."""
        whole_image_score = 0.6
        face_score = 0.7
        forensic_score = 0.3
        forensic_contributions = {
            'ela': 0.4,
            'noise': 0.3,
            'frequency': 0.2,
            'texture': 0.2,
            'edge': 0.3,
            'color': 0.2,
            'exif': 0.1
        }
        
        verdict, confidence, ai_prob, df_prob, final_prob, contributions = _fusion_engine(
            whole_image_score, face_score, forensic_score, forensic_contributions,
            'portrait', 'face'
        )
        
        # Check return types
        assert isinstance(verdict, str)
        assert isinstance(confidence, float)
        assert isinstance(ai_prob, float)
        assert isinstance(df_prob, float)
        assert isinstance(final_prob, float)
        assert isinstance(contributions, dict)
        
        # Check contributions structure
        assert 'whole_image' in contributions
        assert 'face' in contributions
        assert 'forensic' in contributions
        assert 'score' in contributions['whole_image']
        assert 'weight' in contributions['whole_image']
        assert 'contribution' in contributions['whole_image']
    
    def test_fusion_without_faces(self):
        """Test fusion when no faces are detected."""
        whole_image_score = 0.5
        face_score = None
        forensic_score = 0.4
        forensic_contributions = {
            'ela': 0.3,
            'noise': 0.2,
            'frequency': 0.2,
            'texture': 0.2,
            'edge': 0.2,
            'color': 0.2,
            'exif': 0.1
        }
        
        verdict, confidence, ai_prob, df_prob, final_prob, contributions = _fusion_engine(
            whole_image_score, face_score, forensic_score, forensic_contributions,
            'landscape', 'whole_image'
        )
        
        # Check that face contribution is 0 when no faces
        assert contributions['face']['score'] == 0.0
        assert contributions['face']['contribution'] == 0.0
    
    def test_fusion_document_pipeline(self):
        """Test fusion with document pipeline (forensic-heavy)."""
        whole_image_score = 0.3
        face_score = None
        forensic_score = 0.8
        forensic_contributions = {
            'ela': 0.7,
            'noise': 0.6,
            'frequency': 0.7,
            'texture': 0.6,
            'edge': 0.6,
            'color': 0.5,
            'exif': 0.3
        }
        
        verdict, confidence, ai_prob, df_prob, final_prob, contributions = _fusion_engine(
            whole_image_score, face_score, forensic_score, forensic_contributions,
            'document', 'document'
        )
        
        # Document pipeline should give high weight to forensic
        assert contributions['forensic']['weight'] >= 0.5
    
    def test_fusion_verdict_boundaries(self):
        """Test verdict selection at threshold boundaries."""
        forensic_contributions = {
            'ela': 0.5, 'noise': 0.5, 'frequency': 0.5,
            'texture': 0.5, 'edge': 0.5, 'color': 0.5, 'exif': 0.5
        }
        
        # Test deepfake threshold
        verdict, _, _, _, _, _ = _fusion_engine(
            0.9, 0.9, 0.9, forensic_contributions, 'portrait', 'face'
        )
        assert verdict in ['Deepfake', 'AI Generated']
        
        # Test authentic threshold
        verdict, _, _, _, _, _ = _fusion_engine(
            0.1, None, 0.1, forensic_contributions, 'landscape', 'whole_image'
        )
        assert verdict in ['Authentic', 'Likely Authentic']
    
    def test_contributions_calculation(self):
        """Test that contributions are calculated correctly."""
        whole_image_score = 0.5
        face_score = 0.5
        forensic_score = 0.5
        forensic_contributions = {
            'ela': 0.5, 'noise': 0.5, 'frequency': 0.5,
            'texture': 0.5, 'edge': 0.5, 'color': 0.5, 'exif': 0.5
        }
        
        _, _, _, _, _, contributions = _fusion_engine(
            whole_image_score, face_score, forensic_score, forensic_contributions,
            'portrait', 'face'
        )
        
        # Check that contribution = score * weight
        for module in ['whole_image', 'face', 'forensic']:
            expected = contributions[module]['score'] * contributions[module]['weight']
            actual = contributions[module]['contribution']
            assert abs(expected - actual) < 0.001


class TestConfidenceCalibration:
    """Test confidence calibration function."""
    
    def test_confidence_range(self):
        """Test that confidence is always in valid range."""
        for prob in [0.0, 0.25, 0.5, 0.75, 1.0]:
            confidence = _calibrate_confidence(prob)
            assert FusionConfig.CONFIDENCE_CALIBRATION['min_confidence'] <= confidence
            assert confidence <= FusionConfig.CONFIDENCE_CALIBRATION['max_confidence']
    
    def test_confidence_at_boundary(self):
        """Test confidence at decision boundary (0.5)."""
        confidence = _calibrate_confidence(0.5)
        # At 0.5, distance is 0, so confidence should be minimum
        assert confidence == FusionConfig.CONFIDENCE_CALIBRATION['min_confidence']
    
    def test_confidence_monotonic(self):
        """Test that confidence increases with distance from 0.5."""
        conf_0_5 = _calibrate_confidence(0.5)
        conf_0_6 = _calibrate_confidence(0.6)
        conf_0_7 = _calibrate_confidence(0.7)
        
        assert conf_0_5 < conf_0_6 < conf_0_7


class TestExplanationGenerator:
    """Test explanation generation."""
    
    def test_explanation_structure(self):
        """Test that explanation has correct structure."""
        contributions = {
            'whole_image': {'contribution': 0.4, 'score': 0.5, 'weight': 0.8},
            'face': {'contribution': 0.1, 'score': 0.3, 'weight': 0.3},
            'forensic': {
                'contribution': 0.2,
                'score': 0.4,
                'weight': 0.5,
                'sub_modules': {
                    'ela': 0.7,
                    'noise': 0.3,
                    'frequency': 0.2,
                    'texture': 0.2,
                    'edge': 0.2,
                    'color': 0.2,
                    'exif': 0.1
                }
            }
        }
        findings = ["✓ Test finding"]
        
        explanation = _generate_explanation(
            "Suspicious", 0.5, contributions, findings
        )
        
        assert 'for_ai' in explanation
        assert 'against_ai' in explanation
        assert isinstance(explanation['for_ai'], list)
        assert isinstance(explanation['against_ai'], list)
    
    def test_explanation_high_ai_probability(self):
        """Test explanation when AI probability is high."""
        contributions = {
            'whole_image': {'contribution': 0.5, 'score': 0.8, 'weight': 0.6},
            'face': {'contribution': 0.0, 'score': 0.0, 'weight': 0.0},
            'forensic': {
                'contribution': 0.3,
                'score': 0.6,
                'weight': 0.5,
                'sub_modules': {
                    'ela': 0.8, 'noise': 0.7, 'frequency': 0.7,
                    'texture': 0.7, 'edge': 0.6, 'color': 0.5, 'exif': 0.3
                }
            }
        }
        
        explanation = _generate_explanation(
            "AI Generated", 0.8, contributions, []
        )
        
        # Should have evidence for AI
        assert len(explanation['for_ai']) > 0
    
    def test_explanation_low_ai_probability(self):
        """Test explanation when AI probability is low."""
        contributions = {
            'whole_image': {'contribution': 0.1, 'score': 0.2, 'weight': 0.5},
            'face': {'contribution': 0.0, 'score': 0.0, 'weight': 0.0},
            'forensic': {
                'contribution': 0.1,
                'score': 0.2,
                'weight': 0.5,
                'sub_modules': {
                    'ela': 0.2, 'noise': 0.2, 'frequency': 0.2,
                    'texture': 0.2, 'edge': 0.2, 'color': 0.2, 'exif': 0.2
                }
            }
        }
        
        explanation = _generate_explanation(
            "Authentic", 0.2, contributions, []
        )
        
        # Should have evidence against AI
        assert len(explanation['against_ai']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

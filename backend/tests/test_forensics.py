"""
Unit tests for forensic modules.
"""

import pytest
import numpy as np
from PIL import Image
import tempfile
import os
from app.ai.forensics.ela import ela_score


class TestForensics:
    """Test suite for forensic analysis modules."""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        # Create a simple test image
        img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
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
    
    def test_ela_score(self, sample_image_path):
        """Test ELA score calculation."""
        ela_variance, ela_score = ela_score(sample_image_path)
        assert ela_variance is not None
        assert ela_score is not None
        assert ela_variance >= 0
        assert 0 <= ela_score <= 1
    
    def test_ela_score_with_invalid_path(self):
        """Test ELA score with invalid path."""
        with pytest.raises(Exception):
            ela_score("/nonexistent/path/image.jpg")

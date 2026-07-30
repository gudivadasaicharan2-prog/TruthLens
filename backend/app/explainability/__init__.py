"""
Explainability Module for TruthLens
====================================
Module for model explainability and visualization.
"""

from app.explainability.gradcam import GradCAM
from app.explainability.heatmap import generate_heatmap, normalize_heatmap
from app.explainability.overlay import overlay_heatmap, blend_images
from app.explainability.confidence import analyze_confidence, plot_confidence_distribution
from app.explainability.explanation import ExplanationManager

__all__ = [
    'GradCAM',
    'generate_heatmap',
    'normalize_heatmap',
    'overlay_heatmap',
    'blend_images',
    'analyze_confidence',
    'plot_confidence_distribution',
    'ExplanationManager'
]

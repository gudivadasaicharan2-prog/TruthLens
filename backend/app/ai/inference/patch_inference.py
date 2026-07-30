"""
Patch-Based Inference Module for TruthLens v2.2

This module implements patch-based analysis to improve detection of modern AI-generated images
by analyzing local regions at high resolution, which can reveal artifacts that are lost in
global downsampling.

Key features:
- Overlapping patch extraction (256x256, stride 128)
- Batch GPU inference for performance
- Multiple aggregation strategies (max, top-k average, weighted average)
- Patch-level feature extraction for OOD detection
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
from typing import List, Tuple, Dict, Optional
from PIL import Image
import torchvision.transforms as T

# Import existing model infrastructure
from app.ai.models.image_model import get_full_model, _BACKBONE, _CLASSIFIER, _DEVICE


class PatchInference:
    """
    Patch-based inference engine for local artifact detection.
    
    Splits images into overlapping patches and runs EfficientNet on each patch
    to detect local AI generation artifacts that may be missed in global analysis.
    """
    
    def __init__(
        self,
        patch_size: int = 256,
        stride: int = 128,
        min_patch_size: int = 64,
        batch_size: int = 8
    ):
        """
        Initialize patch inference engine.
        
        Args:
            patch_size: Size of each patch (default 256x256)
            stride: Stride between patches (default 128 for 50% overlap)
            min_patch_size: Minimum patch size to keep (discard edge patches)
            batch_size: Batch size for GPU inference
        """
        self.patch_size = patch_size
        self.stride = stride
        self.min_patch_size = min_patch_size
        self.batch_size = batch_size
        
        # Transform for patch preprocessing (same as full image)
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]),
        ])
        
        # Cache for model and device
        self._model = None
        self._device = None
        self._backbone = None
    
    def _get_model(self):
        """Get or initialize the model."""
        if self._model is None or self._device is None:
            self._model = get_full_model()
            self._device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self._model = self._model.to(self._device)
            self._model.eval()
            
            # Get backbone for feature extraction
            self._backbone = nn.Sequential(*list(self._model.children())[:-1])
            self._backbone.eval()
        
        return self._model, self._backbone, self._device
    
    def extract_patches(self, image: np.ndarray) -> List[Tuple[int, int, np.ndarray]]:
        """
        Extract overlapping patches from image.
        
        Args:
            image: Input image as numpy array (H, W, 3) in RGB format
            
        Returns:
            List of (row, col, patch) tuples
        """
        h, w = image.shape[:2]
        patches = []
        
        # Calculate patch positions
        for row in range(0, h - self.patch_size + 1, self.stride):
            for col in range(0, w - self.patch_size + 1, self.stride):
                patch = image[row:row + self.patch_size, col:col + self.patch_size]
                
                # Discard tiny edge patches
                if patch.shape[0] >= self.min_patch_size and patch.shape[1] >= self.min_patch_size:
                    patches.append((row, col, patch))

        
        return patches
    
    def preprocess_patch(self, patch: np.ndarray) -> torch.Tensor:
        """
        Preprocess a single patch for model input.
        
        Args:
            patch: Patch as numpy array (H, W, 3)
            
        Returns:
            Preprocessed tensor (1, 3, 224, 224)
        """
        # Convert to PIL Image
        pil_patch = Image.fromarray(patch.astype(np.uint8))
        
        # Apply transforms
        tensor = self.transform(pil_patch)
        
        # Add batch dimension
        return tensor.unsqueeze(0)
    
    def batch_inference(
        self,
        patches: List[np.ndarray]
    ) -> Tuple[List[float], List[np.ndarray]]:
        """
        Run batch inference on patches.
        
        Args:
            patches: List of patch numpy arrays
            
        Returns:
            (ai_probabilities, feature_vectors)
            ai_probabilities: List of AI probabilities for each patch
            feature_vectors: List of feature vectors for each patch
        """
        model, backbone, device = self._get_model()
        
        # Preprocess all patches
        tensors = [self.preprocess_patch(patch) for patch in patches]
        batch_tensor = torch.cat(tensors, dim=0).to(device)
        
        # Batch inference
        with torch.no_grad():
            # Get features from backbone
            features = backbone(batch_tensor)
            features = features.view(features.size(0), -1)  # Flatten
            
            # Get predictions from full model
            predictions = model(batch_tensor)
            probabilities = predictions.squeeze().cpu().numpy()
        
        # Convert features to numpy
        feature_vectors = features.cpu().numpy()
        
        return probabilities.tolist(), feature_vectors
    
    def analyze_patches(
        self,
        image: np.ndarray
    ) -> Dict:
        """
        Complete patch analysis pipeline.
        
        Args:
            image: Input image as numpy array (H, W, 3) in RGB format
            
        Returns:
            Dictionary containing:
                - number_of_patches: Total patches analyzed
                - patch_probabilities: List of AI probabilities for each patch
                - patch_locations: List of (row, col) for each patch
                - patch_features: Feature vectors for each patch
                - highest_patch_probability: Max AI probability across patches
                - average_patch_probability: Mean AI probability
                - top_k_average: Average of top 5 highest probabilities
                - weighted_average: Average weighted by patch position (center gets higher weight)
                - patch_statistics: Detailed statistics
        """
        # Extract patches
        patches_data = self.extract_patches(image)
        
        if not patches_data:
            return {
                'number_of_patches': 0,
                'patch_probabilities': [],
                'patch_locations': [],
                'patch_features': [],
                'highest_patch_probability': 0.0,
                'average_patch_probability': 0.0,
                'top_k_average': 0.0,
                'weighted_average': 0.0,
                'patch_statistics': {}
            }
        
        # Separate patches and locations
        locations = [(row, col) for row, col, _ in patches_data]
        patches = [patch for _, _, patch in patches_data]
        
        # Batch inference
        probabilities, features = self.batch_inference(patches)
        
        # Calculate statistics
        highest_prob = max(probabilities) if probabilities else 0.0
        average_prob = np.mean(probabilities) if probabilities else 0.0
        
        # Top-k average (k=5)
        k = min(5, len(probabilities))
        top_k_avg = np.mean(sorted(probabilities, reverse=True)[:k]) if probabilities else 0.0
        
        # Weighted average (center patches get higher weight)
        h, w = image.shape[:2]
        center_row, center_col = h // 2, w // 2
        max_dist = np.sqrt(center_row**2 + center_col**2)
        
        weights = []
        for row, col in locations:
            dist = np.sqrt((row - center_row)**2 + (col - center_col)**2)
            weight = 1.0 - (dist / (max_dist + 1e-6))
            weights.append(weight)
        
        weights = np.array(weights)
        weights = weights / (weights.sum() + 1e-6)
        weighted_avg = np.dot(probabilities, weights) if probabilities else 0.0
        
        # Detailed statistics
        patch_stats = {
            'std_deviation': float(np.std(probabilities)) if probabilities else 0.0,
            'median': float(np.median(probabilities)) if probabilities else 0.0,
            'q25': float(np.percentile(probabilities, 25)) if probabilities else 0.0,
            'q75': float(np.percentile(probabilities, 75)) if probabilities else 0.0,
            'high_risk_patches': sum(1 for p in probabilities if p > 0.7),
            'medium_risk_patches': sum(1 for p in probabilities if 0.4 < p <= 0.7),
            'low_risk_patches': sum(1 for p in probabilities if p <= 0.4),
        }
        
        return {
            'number_of_patches': len(patches),
            'patch_probabilities': probabilities,
            'patch_locations': locations,
            'patch_features': features.tolist(),
            'highest_patch_probability': float(highest_prob),
            'average_patch_probability': float(average_prob),
            'top_k_average': float(top_k_avg),
            'weighted_average': float(weighted_avg),
            'patch_statistics': patch_stats
        }


def analyze_image_patches(
    image: np.ndarray,
    patch_size: int = 256,
    stride: int = 128,
    batch_size: int = 8
) -> Dict:
    """
    Convenience function for patch-based analysis.
    
    Args:
        image: Input image as numpy array (H, W, 3) in RGB format
        patch_size: Size of each patch (default 256x256)
        stride: Stride between patches (default 128)
        batch_size: Batch size for GPU inference
        
    Returns:
        Dictionary containing patch analysis results
    """
    engine = PatchInference(patch_size=patch_size, stride=stride, batch_size=batch_size)
    return engine.analyze_patches(image)

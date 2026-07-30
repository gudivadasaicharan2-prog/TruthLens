"""
Out-of-Distribution (OOD) Detector for TruthLens v2.2

This module implements OOD detection using feature statistics from the training distribution.
When an image's features are far from the known distribution, it increases uncertainty instead
of incorrectly predicting "Real".

Key features:
- Mahalanobis distance to training feature centroid
- Cosine distance to training feature centroid
- Known distribution probability estimation
- Adaptive uncertainty scaling for OOD samples
- New verdict: "Unknown Generation Method" when appropriate
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Optional, Tuple
from sklearn.covariance import EmpiricalCovariance
from scipy.spatial.distance import mahalanobis, cosine


class OODDetector:
    """
    Out-of-Distribution detector using feature statistics.
    
    Detects when an image's features are outside the known training distribution
    and increases uncertainty instead of making incorrect predictions.
    """
    
    def __init__(
        self,
        feature_dim: int = 1408,  # EfficientNet-B2 feature dimension
        mahalanobis_threshold: float = 3.0,
        cosine_threshold: float = 0.3,
        enable_mahalanobis: bool = True,
        enable_cosine: bool = True
    ):
        """
        Initialize OOD detector.
        
        Args:
            feature_dim: Dimension of feature vectors
            mahalanobis_threshold: Threshold for Mahalanobis distance (higher = more permissive)
            cosine_threshold: Threshold for cosine distance (higher = more permissive)
            enable_mahalanobis: Whether to use Mahalanobis distance
            enable_cosine: Whether to use cosine distance
        """
        self.feature_dim = feature_dim
        self.mahalanobis_threshold = mahalanobis_threshold
        self.cosine_threshold = cosine_threshold
        self.enable_mahalanobis = enable_mahalanobis
        self.enable_cosine = enable_cosine
        
        # Training distribution statistics (initialized with reasonable defaults)
        # These would normally be computed from the training set
        self.feature_mean = np.zeros(feature_dim)
        self.feature_cov = np.eye(feature_dim)
        self.covariance_estimator = EmpiricalCovariance()
        self._statistics_computed = False
    
    def compute_statistics(self, features: np.ndarray):
        """
        Compute feature statistics from training data.
        
        Args:
            features: Array of shape (n_samples, feature_dim) from training set
        """
        if features.shape[0] == 0:
            return
        
        # Compute mean
        self.feature_mean = np.mean(features, axis=0)
        
        # Compute covariance matrix
        self.covariance_estimator.fit(features)
        self.feature_cov = self.covariance_estimator.covariance_
        
        # Add small regularization for numerical stability
        self.feature_cov += np.eye(self.feature_dim) * 1e-6
        
        self._statistics_computed = True
    
    def mahalanobis_distance(self, feature: np.ndarray) -> float:
        """
        Compute Mahalanobis distance to training distribution.
        
        Args:
            feature: Feature vector of shape (feature_dim,)
            
        Returns:
            Mahalanobis distance
        """
        if not self._statistics_computed:
            return 0.0
        
        try:
            # Compute inverse covariance matrix
            inv_cov = np.linalg.inv(self.feature_cov)
            
            # Compute Mahalanobis distance
            diff = feature - self.feature_mean
            distance = np.sqrt(diff @ inv_cov @ diff.T)
            
            return float(distance)
        except Exception:
            return 0.0
    
    def cosine_distance(self, feature: np.ndarray) -> float:
        """
        Compute cosine distance to training distribution mean.
        
        Args:
            feature: Feature vector of shape (feature_dim,)
            
        Returns:
            Cosine distance (1 - cosine similarity)
        """
        if not self._statistics_computed:
            return 0.0
        
        try:
            # Compute cosine similarity
            similarity = np.dot(feature, self.feature_mean) / (
                np.linalg.norm(feature) * np.linalg.norm(self.feature_mean) + 1e-8
            )
            
            # Convert to distance
            distance = 1.0 - similarity
            
            return float(distance)
        except Exception:
            return 0.0
    
    def compute_ood_score(
        self,
        feature: np.ndarray,
        patch_features: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Compute OOD score for a single feature vector.
        
        Args:
            feature: Feature vector of shape (feature_dim,)
            patch_features: Optional array of patch features for ensemble scoring
            
        Returns:
            Dictionary containing:
                - ood_score: Combined OOD score (0 = in-distribution, 1 = OOD)
                - mahalanobis_distance: Mahalanobis distance
                - cosine_distance: Cosine distance
                - known_distribution_probability: Probability of being in known distribution
                - is_ood: Boolean indicating if sample is OOD
        """
        scores = {}
        
        # Mahalanobis distance
        if self.enable_mahalanobis:
            mahal_dist = self.mahalanobis_distance(feature)
            scores['mahalanobis_distance'] = mahal_dist
            # Normalize to [0, 1] using threshold
            mahal_score = min(mahal_dist / self.mahalanobis_threshold, 1.0)
        else:
            scores['mahalanobis_distance'] = 0.0
            mahal_score = 0.0
        
        # Cosine distance
        if self.enable_cosine:
            cos_dist = self.cosine_distance(feature)
            scores['cosine_distance'] = cos_dist
            # Normalize to [0, 1] using threshold
            cos_score = min(cos_dist / self.cosine_threshold, 1.0)
        else:
            scores['cosine_distance'] = 0.0
            cos_score = 0.0
        
        # Combine scores
        if self.enable_mahalanobis and self.enable_cosine:
            combined_score = (mahal_score + cos_score) / 2.0
        elif self.enable_mahalanobis:
            combined_score = mahal_score
        else:
            combined_score = cos_score
        
        scores['ood_score'] = combined_score
        scores['known_distribution_probability'] = 1.0 - combined_score
        scores['is_ood'] = combined_score > 0.5
        
        # Ensemble with patch features if available
        if patch_features is not None and len(patch_features) > 0:
            patch_ood_scores = []
            for patch_feat in patch_features:
                patch_score = self.compute_ood_score(patch_feat)
                patch_ood_scores.append(patch_score['ood_score'])
            
            # Average patch OOD score
            avg_patch_ood = np.mean(patch_ood_scores)
            
            # Combine global and patch scores (weighted average)
            scores['patch_ood_score'] = float(avg_patch_ood)
            scores['ood_score'] = 0.6 * combined_score + 0.4 * avg_patch_ood
            scores['known_distribution_probability'] = 1.0 - scores['ood_score']
            scores['is_ood'] = scores['ood_score'] > 0.5
        
        return scores
    
    def adjust_prediction(
        self,
        fake_probability: float,
        ood_score: float
    ) -> Tuple[float, str]:
        """
        Adjust prediction based on OOD score.
        
        When a sample is OOD, increase uncertainty instead of making
        incorrect predictions.
        
        Args:
            fake_probability: Original fake probability [0, 1]
            ood_score: OOD score [0, 1]
            
        Returns:
            (adjusted_probability, suggested_verdict)
        """
        if ood_score < 0.3:
            # In-distribution: keep original prediction
            return fake_probability, None
        elif ood_score < 0.5:
            # Slightly OOD: moderate adjustment toward uncertainty
            adjusted = fake_probability * 0.7 + 0.5 * 0.3
            return adjusted, None
        elif ood_score < 0.7:
            # Moderately OOD: strong adjustment toward uncertainty
            adjusted = fake_probability * 0.4 + 0.5 * 0.6
            return adjusted, "Unknown Generation Method"
        else:
            # Highly OOD: very uncertain
            adjusted = 0.5
            return adjusted, "Unknown Generation Method"


# Global OOD detector instance
_ood_detector = None


def get_ood_detector() -> OODDetector:
    """
    Get or create the global OOD detector instance.
    
    Returns:
        OODDetector instance
    """
    global _ood_detector
    if _ood_detector is None:
        _ood_detector = OODDetector()
    return _ood_detector


def detect_ood(
    feature: np.ndarray,
    patch_features: Optional[np.ndarray] = None
) -> Dict:
    """
    Convenience function for OOD detection.
    
    Args:
        feature: Feature vector of shape (feature_dim,)
        patch_features: Optional array of patch features
        
    Returns:
        Dictionary containing OOD detection results
    """
    detector = get_ood_detector()
    return detector.compute_ood_score(feature, patch_features)


def adjust_for_ood(
    fake_probability: float,
    ood_score: float
) -> Tuple[float, Optional[str]]:
    """
    Convenience function for adjusting predictions based on OOD.
    
    Args:
        fake_probability: Original fake probability
        ood_score: OOD score
        
    Returns:
        (adjusted_probability, suggested_verdict)
    """
    detector = get_ood_detector()
    return detector.adjust_prediction(fake_probability, ood_score)

"""
Confidence Calibration Module for TruthLens v2.2

This module implements temperature scaling for confidence calibration
without requiring model retraining. Temperature scaling is a post-hoc
calibration method that adjusts model outputs to better reflect true
probabilities.

Key features:
- Temperature scaling (T > 1 softens, T < 1 sharpens)
- Adaptive temperature based on OOD score
- Platt scaling alternative
- Multi-verdict calibration
"""

import numpy as np
import math
from typing import Tuple, Optional

# Import configuration
from app.ai.detectors.fusion_config import FusionConfig


class ConfidenceCalibrator:
    """
    Confidence calibrator using temperature scaling.
    
    Temperature scaling adjusts the softmax temperature to calibrate
    model confidence without retraining. This is particularly useful
    for handling out-of-distribution samples.
    """
    
    def __init__(self, temperature: float = 1.0, adaptive: bool = True):
        """
        Initialize confidence calibrator.
        
        Args:
            temperature: Scaling temperature (default 1.0 = no scaling)
            adaptive: Whether to adapt temperature based on OOD score
        """
        self.temperature = temperature
        self.adaptive = adaptive
        self.config = FusionConfig.TEMPERATURE_SCALING
    
    def apply_temperature_scaling(
        self,
        logit: float,
        temperature: Optional[float] = None
    ) -> float:
        """
        Apply temperature scaling to a logit.
        
        Args:
            logit: Raw model logit (before sigmoid)
            temperature: Temperature to use (overrides instance temperature)
            
        Returns:
            Scaled probability
        """
        if temperature is None:
            temperature = self.temperature
        
        if temperature == 1.0:
            # No scaling
            return 1.0 / (1.0 + math.exp(-logit))
        
        # Apply temperature scaling
        scaled_logit = logit / temperature
        return 1.0 / (1.0 + math.exp(-scaled_logit))
    
    def get_adaptive_temperature(self, ood_score: float) -> float:
        """
        Get adaptive temperature based on OOD score.
        
        Higher OOD score (more uncertain) -> higher temperature (softer predictions)
        Lower OOD score (more confident) -> lower temperature (sharper predictions)
        
        Args:
            ood_score: OOD score [0, 1] where 1 = highly OOD
            
        Returns:
            Adaptive temperature
        """
        if not self.adaptive:
            return self.temperature
        
        # Map OOD score to temperature range
        # OOD 0.0 -> min_temperature (sharper)
        # OOD 1.0 -> max_temperature (softer)
        min_temp = self.config['min_temperature']
        max_temp = self.config['max_temperature']
        
        adaptive_temp = min_temp + ood_score * (max_temp - min_temp)
        
        return adaptive_temp
    
    def calibrate_probability(
        self,
        probability: float,
        ood_score: float = 0.0
    ) -> Tuple[float, float]:
        """
        Calibrate a probability using temperature scaling.
        
        Args:
            probability: Original probability [0, 1]
            ood_score: OOD score [0, 1] for adaptive scaling
            
        Returns:
            (calibrated_probability, temperature_used)
        """
        # Convert probability to logit
        # Avoid log(0) by clamping
        probability_clamped = max(min(probability, 0.9999), 0.0001)
        logit = math.log(probability_clamped / (1.0 - probability_clamped))
        
        # Get adaptive temperature
        temperature = self.get_adaptive_temperature(ood_score)
        
        # Apply temperature scaling
        calibrated_prob = self.apply_temperature_scaling(logit, temperature)
        
        return calibrated_prob, temperature
    
    def calibrate_with_verdict(
        self,
        fake_prob: float,
        verdict: str,
        ood_score: float = 0.0
    ) -> Tuple[float, float, str]:
        """
        Calibrate probability with verdict-specific adjustments.
        
        Different verdicts may require different calibration strategies.
        For example, "Unknown Generation Method" should have higher uncertainty.
        
        Args:
            fake_prob: Original fake probability [0, 1]
            verdict: Current verdict
            ood_score: OOD score [0, 1]
            
        Returns:
            (calibrated_probability, temperature_used, adjusted_verdict)
        """
        # Apply temperature scaling
        calibrated_prob, temperature = self.calibrate_probability(fake_prob, ood_score)
        
        # Adjust verdict based on OOD score
        if ood_score > 0.7 and verdict != "Unknown Generation Method":
            # Highly OOD: increase uncertainty
            adjusted_verdict = "Unknown Generation Method"
        elif ood_score > 0.5:
            # Moderately OOD: soften verdict
            if verdict == "AI Generated":
                adjusted_verdict = "Suspicious"
            elif verdict == "Deepfake":
                adjusted_verdict = "Suspicious"
            elif verdict == "Authentic":
                adjusted_verdict = "Likely Authentic"
            else:
                adjusted_verdict = verdict
        else:
            adjusted_verdict = verdict
        
        return calibrated_prob, temperature, adjusted_verdict


# Global calibrator instance
_calibrator = None


def get_calibrator() -> ConfidenceCalibrator:
    """
    Get or create the global confidence calibrator instance.
    
    Returns:
        ConfidenceCalibrator instance
    """
    global _calibrator
    if _calibrator is None:
        config = FusionConfig.TEMPERATURE_SCALING
        _calibrator = ConfidenceCalibrator(
            temperature=config['temperature'],
            adaptive=config['adaptive_temperature']
        )
    return _calibrator


def calibrate_confidence(
    probability: float,
    ood_score: float = 0.0
) -> Tuple[float, float]:
    """
    Convenience function for confidence calibration.
    
    Args:
        probability: Original probability [0, 1]
        ood_score: OOD score [0, 1]
        
    Returns:
        (calibrated_probability, temperature_used)
    """
    calibrator = get_calibrator()
    return calibrator.calibrate_probability(probability, ood_score)


def calibrate_with_verdict(
    fake_prob: float,
    verdict: str,
    ood_score: float = 0.0
) -> Tuple[float, float, str]:
    """
    Convenience function for verdict-aware calibration.
    
    Args:
        fake_prob: Original fake probability
        verdict: Current verdict
        ood_score: OOD score
        
    Returns:
        (calibrated_probability, temperature_used, adjusted_verdict)
    """
    calibrator = get_calibrator()
    return calibrator.calibrate_with_verdict(fake_prob, verdict, ood_score)


def enhanced_confidence_calibration(
    fake_prob: float,
    ood_score: float = 0.0,
    patch_stats: Optional[dict] = None
) -> dict:
    """
    Enhanced confidence calibration using multiple signals.
    
    Combines temperature scaling with patch statistics and OOD detection
    for more robust confidence estimation.
    
    Args:
        fake_prob: Original fake probability
        ood_score: OOD score
        patch_stats: Optional patch statistics from patch inference
        
    Returns:
        Dictionary containing:
            - calibrated_probability: Calibrated fake probability
            - temperature: Temperature used for scaling
            - confidence_level: Textual confidence level
            - uncertainty: Estimated uncertainty
            - adjustment_factors: Factors that influenced calibration
    """
    calibrator = get_calibrator()
    
    # Base temperature scaling
    calibrated_prob, temperature = calibrator.calibrate_probability(fake_prob, ood_score)
    
    # Additional adjustments based on patch statistics
    adjustment_factors = {
        'ood_score': ood_score,
        'temperature': temperature
    }
    
    if patch_stats:
        # Use patch statistics to adjust confidence
        # High variance in patch probabilities = higher uncertainty
        patch_std = patch_stats.get('patch_statistics', {}).get('std_deviation', 0.0)
        adjustment_factors['patch_std'] = patch_std
        
        # If patch probabilities are highly variable, increase uncertainty
        if patch_std > 0.3:
            # Soften the probability
            calibrated_prob = 0.5 + (calibrated_prob - 0.5) * 0.7
            adjustment_factors['patch_adjustment'] = 'softened'
        elif patch_std < 0.1:
            # Patch probabilities are consistent - sharpen
            calibrated_prob = 0.5 + (calibrated_prob - 0.5) * 1.1
            adjustment_factors['patch_adjustment'] = 'sharpened'
    
    # Compute confidence level
    distance_from_50 = abs(calibrated_prob - 0.5)
    if distance_from_50 > 0.4:
        confidence_level = "High"
    elif distance_from_50 > 0.25:
        confidence_level = "Medium"
    elif distance_from_50 > 0.15:
        confidence_level = "Low"
    else:
        confidence_level = "Very Low"
    
    # Estimate uncertainty
    uncertainty = 1.0 - distance_from_50 * 2.0  # [0, 1]
    uncertainty = max(min(uncertainty, 1.0), 0.0)
    
    return {
        'calibrated_probability': float(calibrated_prob),
        'temperature': float(temperature),
        'confidence_level': confidence_level,
        'uncertainty': float(uncertainty),
        'adjustment_factors': adjustment_factors
    }

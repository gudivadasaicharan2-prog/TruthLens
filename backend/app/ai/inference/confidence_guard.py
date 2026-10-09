"""
Confidence Guard Layer - TruthLens v2.3

Implements final confidence refinement after fusion.
If classifier predicts "Likely Authentic" with high confidence but multiple
forensic modules disagree, automatically reduce confidence.

This prevents false negatives where the classifier is overconfident
but forensic analysis reveals anomalies.
"""

import numpy as np
from typing import Dict, Tuple, Optional


class ConfidenceGuard:
    """
    Confidence Guard Layer for v2.3
    
    Performs weighted confidence correction based on:
    - Classifier confidence
    - Forensic module disagreement
    - CLIP AI score
    - Patch consensus disagreement
    - OOD score
    """
    
    # Thresholds for confidence guard activation
    HIGH_CLASSIFIER_CONFIDENCE = 0.80
    FORENSIC_ANOMALY_THRESHOLD = 0.70
    CLIP_AI_THRESHOLD = 0.75
    PATCH_DISAGREEMENT_THRESHOLD = 0.30
    OOD_THRESHOLD = 0.65
    
    # Confidence reduction factors
    FORENSIC_DISAGREEMENT_PENALTY = 0.15
    CLIP_DISAGREEMENT_PENALTY = 0.12
    PATCH_DISAGREEMENT_PENALTY = 0.10
    OOD_PENALTY = 0.08
    
    @staticmethod
    def apply_guard(
        classifier_confidence: float,
        classifier_verdict: str,
        forensic_score: float,
        forensic_contributions: Dict[str, float],
        clip_score: Optional[float] = None,
        patch_consensus_score: Optional[float] = None,
        ood_score: Optional[float] = None
    ) -> Tuple[float, str, Dict[str, float]]:
        """
        Apply confidence guard to refine final confidence and verdict.
        
        Args:
            classifier_confidence: Original confidence from fusion
            classifier_verdict: Original verdict from fusion
            forensic_score: Overall forensic anomaly score (0-1, 1=fake)
            forensic_contributions: Individual forensic module scores
            clip_score: CLIP AI probability (0-1, 1=AI)
            patch_consensus_score: Patch consensus agreement (0-1, 1=high agreement)
            ood_score: OOD detection score (0-1, 1=high OOD)
            
        Returns:
            Tuple of (adjusted_confidence, adjusted_verdict, adjustment_details)
        """
        adjustment_details = {
            'original_confidence': classifier_confidence,
            'original_verdict': classifier_verdict,
            'confidence_adjustment': 0.0,
            'adjustment_reasons': []
        }
        
        # Only apply guard if classifier is overconfident about authenticity
        if (classifier_verdict in ['Likely Authentic', 'Authentic'] and 
            classifier_confidence > ConfidenceGuard.HIGH_CLASSIFIER_CONFIDENCE):
            
            total_penalty = 0.0
            
            # Check forensic disagreement
            forensic_disagreement = ConfidenceGuard._check_forensic_disagreement(
                forensic_score, forensic_contributions
            )
            if forensic_disagreement:
                total_penalty += ConfidenceGuard.FORENSIC_DISAGREEMENT_PENALTY
                adjustment_details['adjustment_reasons'].append(
                    f"Forensic modules show anomalies (score: {forensic_score:.3f})"
                )
            
            # Check CLIP disagreement
            if clip_score is not None and clip_score > ConfidenceGuard.CLIP_AI_THRESHOLD:
                total_penalty += ConfidenceGuard.CLIP_DISAGREEMENT_PENALTY
                adjustment_details['adjustment_reasons'].append(
                    f"CLIP semantic analysis indicates AI (score: {clip_score:.3f})"
                )
            
            # Check patch disagreement
            if (patch_consensus_score is not None and 
                patch_consensus_score < (1.0 - ConfidenceGuard.PATCH_DISAGREEMENT_THRESHOLD)):
                total_penalty += ConfidenceGuard.PATCH_DISAGREEMENT_PENALTY
                adjustment_details['adjustment_reasons'].append(
                    f"Patch consensus disagreement (score: {patch_consensus_score:.3f})"
                )
            
            # Check OOD score
            if ood_score is not None and ood_score > ConfidenceGuard.OOD_THRESHOLD:
                total_penalty += ConfidenceGuard.OOD_PENALTY
                adjustment_details['adjustment_reasons'].append(
                    f"Out-of-distribution detection (score: {ood_score:.3f})"
                )
            
            # Apply penalty if significant disagreement detected
            if total_penalty > 0.0:
                # Cap penalty to avoid over-correction
                total_penalty = min(total_penalty, 0.35)
                adjusted_confidence = classifier_confidence - total_penalty
                adjusted_confidence = max(adjusted_confidence, 0.50)  # Minimum confidence
                
                adjustment_details['confidence_adjustment'] = -total_penalty
                
                # Adjust verdict if confidence drops significantly
                if adjusted_confidence < 0.65:
                    adjusted_verdict = "Suspicious"
                elif adjusted_confidence < 0.75:
                    adjusted_verdict = "Likely Authentic"
                else:
                    adjusted_verdict = classifier_verdict
            else:
                adjusted_confidence = classifier_confidence
                adjusted_verdict = classifier_verdict
        else:
            adjusted_confidence = classifier_confidence
            adjusted_verdict = classifier_verdict
        
        adjustment_details['adjusted_confidence'] = adjusted_confidence
        adjustment_details['adjusted_verdict'] = adjusted_verdict
        
        return adjusted_confidence, adjusted_verdict, adjustment_details
    
    @staticmethod
    def _check_forensic_disagreement(
        forensic_score: float,
        forensic_contributions: Dict[str, float]
    ) -> bool:
        """
        Check if multiple forensic modules show disagreement with authentic verdict.
        
        Args:
            forensic_score: Overall forensic anomaly score
            forensic_contributions: Individual module scores
            
        Returns:
            True if significant forensic disagreement detected
        """
        # High overall forensic anomaly
        if forensic_score > ConfidenceGuard.FORENSIC_ANOMALY_THRESHOLD:
            return True
        
        # Count individual module anomalies
        anomaly_count = 0
        for module, score in forensic_contributions.items():
            if score > 0.70:  # Individual module threshold
                anomaly_count += 1
        
        # If 2+ modules show anomalies, consider it disagreement
        return anomaly_count >= 2
    
    @staticmethod
    def get_dominant_signal(
        forensic_score: float,
        clip_score: Optional[float],
        patch_consensus: Optional[float],
        ood_score: Optional[float],
        diffusion_score: Optional[float]
    ) -> Tuple[str, str]:
        """
        Identify the dominant and secondary signals driving the decision.
        
        Args:
            forensic_score: Forensic anomaly score
            clip_score: CLIP AI score
            patch_consensus: Patch consensus score
            ood_score: OOD score
            diffusion_score: Diffusion fingerprint score
            
        Returns:
            Tuple of (dominant_signal, secondary_signal)
        """
        signals = {
            'forensic_anomaly': forensic_score,
            'clip_semantic': clip_score if clip_score else 0.0,
            'patch_consensus': 1.0 - patch_consensus if patch_consensus else 0.0,
            'ood_detection': ood_score if ood_score else 0.0,
            'diffusion_fingerprint': diffusion_score if diffusion_score else 0.0
        }
        
        # Sort by score (descending)
        sorted_signals = sorted(signals.items(), key=lambda x: x[1], reverse=True)
        
        dominant = sorted_signals[0][0] if sorted_signals[0][1] > 0.5 else "classifier"
        secondary = sorted_signals[1][0] if len(sorted_signals) > 1 and sorted_signals[1][1] > 0.5 else "none"
        
        return dominant, secondary

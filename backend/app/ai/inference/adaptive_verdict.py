"""
Adaptive Verdict Logic - TruthLens v2.3

Implements multi-signal verdict logic that considers:
- Classifier confidence
- Forensic analysis
- CLIP semantic verification
- Patch consensus
- OOD score
- Diffusion fingerprint
- Confidence calibration

Instead of relying mostly on classifier confidence, the final verdict
considers all available signals to make a more robust decision.
"""

import numpy as np
from typing import Dict, Tuple, Optional


class AdaptiveVerdict:
    """
    Adaptive verdict engine for v2.3
    
    Combines multiple detection signals into a final verdict using
    weighted decision logic rather than simple classifier confidence.
    """
    
    # Signal thresholds
    CLASSIFIER_AI_THRESHOLD = 0.65
    FORENSIC_ANOMALY_THRESHOLD = 0.70
    CLIP_AI_THRESHOLD = 0.75
    PATCH_AI_THRESHOLD = 0.70
    OOD_THRESHOLD = 0.65
    DIFFUSION_THRESHOLD = 0.70
    
    # Verdict thresholds (adjusted for multi-signal logic)
    VERDICT_THRESHOLDS = {
        'deepfake': 0.85,
        'ai_generated': 0.72,
        'suspicious': 0.55,
        'likely_authentic': 0.40,
        'authentic': 0.00
    }
    
    # Signal weights for adaptive verdict
    SIGNAL_WEIGHTS = {
        'classifier': 0.25,
        'forensic': 0.25,
        'clip': 0.15,
        'patch': 0.15,
        'ood': 0.10,
        'diffusion': 0.10
    }
    
    @staticmethod
    def compute_adaptive_verdict(
        classifier_score: float,
        forensic_score: float,
        clip_ai_score: Optional[float] = None,
        patch_consensus_score: Optional[float] = None,
        ood_score: Optional[float] = None,
        diffusion_score: Optional[float] = None,
        has_faces: bool = False,
        image_type: str = "photo"
    ) -> Tuple[str, float, Dict]:
        """
        Compute adaptive verdict considering all available signals.
        
        Args:
            classifier_score: EfficientNet classifier score (0-1, 1=fake)
            forensic_score: Forensic anomaly score (0-1, 1=fake)
            clip_ai_score: CLIP AI semantic score (0-1, 1=AI)
            patch_consensus_score: Patch consensus (0-1, 1=high agreement)
            ood_score: OOD detection score (0-1, 1=high OOD)
            diffusion_score: Diffusion fingerprint score (0-1, 1=diffusion)
            has_faces: Whether faces were detected
            image_type: Type of image (portrait, landscape, artwork, etc.)
            
        Returns:
            Tuple of (verdict, confidence, signal_analysis)
        """
        signal_analysis = {
            'classifier_signal': AdaptiveVerdict._classify_signal(classifier_score, AdaptiveVerdict.CLASSIFIER_AI_THRESHOLD),
            'forensic_signal': AdaptiveVerdict._classify_signal(forensic_score, AdaptiveVerdict.FORENSIC_ANOMALY_THRESHOLD),
            'clip_signal': AdaptiveVerdict._classify_optional_signal(clip_ai_score, AdaptiveVerdict.CLIP_AI_THRESHOLD),
            'patch_signal': AdaptiveVerdict._classify_optional_signal(patch_consensus_score, AdaptiveVerdict.PATCH_AI_THRESHOLD, invert=True),
            'ood_signal': AdaptiveVerdict._classify_optional_signal(ood_score, AdaptiveVerdict.OOD_THRESHOLD),
            'diffusion_signal': AdaptiveVerdict._classify_optional_signal(diffusion_score, AdaptiveVerdict.DIFFUSION_THRESHOLD),
        }
        
        # Count AI signals vs Authentic signals
        ai_signals = sum(1 for s in signal_analysis.values() if s == 'ai')
        authentic_signals = sum(1 for s in signal_analysis.values() if s == 'authentic')
        neutral_signals = sum(1 for s in signal_analysis.values() if s == 'neutral')
        
        # Calculate weighted score
        weighted_score = AdaptiveVerdict._calculate_weighted_score(
            classifier_score, forensic_score, clip_ai_score,
            patch_consensus_score, ood_score, diffusion_score
        )
        
        # Adjust based on signal agreement
        signal_agreement = AdaptiveVerdict._calculate_signal_agreement(signal_analysis)
        
        # Final score combines weighted score and signal agreement
        final_score = weighted_score * 0.7 + signal_agreement * 0.3
        
        # Determine verdict
        verdict = AdaptiveVerdict._determine_verdict(
            final_score, ai_signals, authentic_signals, neutral_signals, has_faces, image_type
        )
        
        # Calculate confidence
        confidence = AdaptiveVerdict._calculate_confidence(
            final_score, signal_agreement, ai_signals, authentic_signals
        )
        
        signal_analysis['ai_signal_count'] = ai_signals
        signal_analysis['authentic_signal_count'] = authentic_signals
        signal_analysis['neutral_signal_count'] = neutral_signals
        signal_analysis['weighted_score'] = weighted_score
        signal_analysis['signal_agreement'] = signal_agreement
        signal_analysis['final_score'] = final_score
        
        return verdict, confidence, signal_analysis
    
    @staticmethod
    def _classify_signal(score: float, threshold: float) -> str:
        """
        Classify a signal as AI, authentic, or neutral.
        
        Args:
            score: Signal score (0-1)
            threshold: Threshold for AI classification
            
        Returns:
            'ai', 'authentic', or 'neutral'
        """
        if score > threshold:
            return 'ai'
        elif score < (1.0 - threshold):
            return 'authentic'
        else:
            return 'neutral'
    
    @staticmethod
    def _classify_optional_signal(
        score: Optional[float],
        threshold: float,
        invert: bool = False
    ) -> str:
        """
        Classify an optional signal (may be None).
        
        Args:
            score: Signal score (0-1) or None
            threshold: Threshold for classification
            invert: If True, invert the score (for consensus scores)
            
        Returns:
            'ai', 'authentic', 'neutral', or 'unavailable'
        """
        if score is None:
            return 'unavailable'
        
        if invert:
            # For consensus scores, lower = more disagreement = AI
            adjusted_score = 1.0 - score
        else:
            adjusted_score = score
        
        return AdaptiveVerdict._classify_signal(adjusted_score, threshold)
    
    @staticmethod
    def _calculate_weighted_score(
        classifier_score: float,
        forensic_score: float,
        clip_ai_score: Optional[float] = None,
        patch_consensus_score: Optional[float] = None,
        ood_score: Optional[float] = None,
        diffusion_score: Optional[float] = None
    ) -> float:
        """
        Calculate weighted score from all signals.
        
        Args:
            classifier_score: Classifier score
            forensic_score: Forensic score
            clip_ai_score: CLIP AI score
            patch_consensus_score: Patch consensus
            ood_score: OOD score
            diffusion_score: Diffusion score
            
        Returns:
            Weighted score [0, 1]
        """
        scores = {
            'classifier': classifier_score,
            'forensic': forensic_score,
            'clip': clip_ai_score if clip_ai_score is not None else 0.5,
            'patch': 1.0 - patch_consensus_score if patch_consensus_score is not None else 0.5,
            'ood': ood_score if ood_score is not None else 0.5,
            'diffusion': diffusion_score if diffusion_score is not None else 0.5
        }
        
        # Normalize weights based on available signals
        available_weights = {}
        total_weight = 0.0
        
        for signal, weight in AdaptiveVerdict.SIGNAL_WEIGHTS.items():
            if scores[signal] is not None:
                available_weights[signal] = weight
                total_weight += weight
        
        # Normalize weights
        if total_weight > 0:
            for signal in available_weights:
                available_weights[signal] /= total_weight
        
        # Calculate weighted score
        weighted_score = sum(
            scores[signal] * available_weights[signal]
            for signal in available_weights
        )
        
        return weighted_score
    
    @staticmethod
    def _calculate_signal_agreement(signal_analysis: Dict) -> float:
        """
        Calculate how much signals agree with each other.
        
        Args:
            signal_analysis: Dictionary of signal classifications
            
        Returns:
            Agreement score [0, 1] where higher = more agreement
        """
        available_signals = [
            s for s in signal_analysis.values()
            if s in ['ai', 'authentic']
        ]
        
        if not available_signals:
            return 0.5  # Neutral if no signals available
        
        # Count AI and authentic signals
        ai_count = sum(1 for s in available_signals if s == 'ai')
        authentic_count = sum(1 for s in available_signals if s == 'authentic')
        
        total = len(available_signals)
        
        # Agreement is the proportion of the dominant signal
        dominant_count = max(ai_count, authentic_count)
        agreement = dominant_count / total
        
        return agreement
    
    @staticmethod
    def _determine_verdict(
        final_score: float,
        ai_signals: int,
        authentic_signals: int,
        neutral_signals: int,
        has_faces: bool,
        image_type: str
    ) -> str:
        """
        Determine final verdict based on score and signal counts.
        
        Args:
            final_score: Final weighted score
            ai_signals: Number of AI signals
            authentic_signals: Number of authentic signals
            neutral_signals: Number of neutral signals
            has_faces: Whether faces were detected
            image_type: Image type
            
        Returns:
            Verdict string
        """
        # Check for deepfake (face + strong AI signals)
        if has_faces and ai_signals >= 3 and final_score > AdaptiveVerdict.VERDICT_THRESHOLDS['deepfake']:
            return "Deepfake"
        
        # Check for AI generated
        if final_score > AdaptiveVerdict.VERDICT_THRESHOLDS['ai_generated']:
            return "AI Generated"
        
        # Check for suspicious
        if final_score > AdaptiveVerdict.VERDICT_THRESHOLDS['suspicious']:
            return "Suspicious"
        
        # Check for likely authentic
        if final_score > AdaptiveVerdict.VERDICT_THRESHOLDS['likely_authentic']:
            return "Likely Authentic"
        
        # Otherwise authentic
        return "Authentic"
    
    @staticmethod
    def _calculate_confidence(
        final_score: float,
        signal_agreement: float,
        ai_signals: int,
        authentic_signals: int
    ) -> float:
        """
        Calculate confidence in the verdict.
        
        Args:
            final_score: Final weighted score
            signal_agreement: Signal agreement score
            ai_signals: Number of AI signals
            authentic_signals: Number of authentic signals
            
        Returns:
            Confidence score [0, 1]
        """
        # Base confidence from distance from 0.5
        distance_from_neutral = abs(final_score - 0.5) * 2
        
        # Boost confidence if signals agree
        agreement_boost = signal_agreement * 0.2
        
        # Boost confidence if signals are decisive
        signal_decisiveness = max(ai_signals, authentic_signals) / (ai_signals + authentic_signals + 1)
        decisiveness_boost = signal_decisiveness * 0.1
        
        # Combine factors
        confidence = distance_from_neutral * 0.7 + agreement_boost + decisiveness_boost
        
        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence


def compute_adaptive_verdict(
    classifier_score: float,
    forensic_score: float,
    clip_ai_score: Optional[float] = None,
    patch_consensus_score: Optional[float] = None,
    ood_score: Optional[float] = None,
    diffusion_score: Optional[float] = None,
    has_faces: bool = False,
    image_type: str = "photo"
) -> Tuple[str, float, Dict]:
    """
    Convenience function for adaptive verdict computation.
    
    Args:
        classifier_score: EfficientNet classifier score
        forensic_score: Forensic anomaly score
        clip_ai_score: CLIP AI semantic score
        patch_consensus_score: Patch consensus
        ood_score: OOD detection score
        diffusion_score: Diffusion fingerprint score
        has_faces: Whether faces were detected
        image_type: Type of image
        
    Returns:
        Tuple of (verdict, confidence, signal_analysis)
    """
    return AdaptiveVerdict.compute_adaptive_verdict(
        classifier_score, forensic_score, clip_ai_score,
        patch_consensus_score, ood_score, diffusion_score,
        has_faces, image_type
    )

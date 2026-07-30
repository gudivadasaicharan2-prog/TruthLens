"""
Enhanced Explainability Module for TruthLens v2.2

This module provides comprehensive explainability features for AI detection results,
including patch-level analysis, natural language explanations, and detailed
forensic contribution breakdowns.

Key features:
- Top suspicious patches identification
- Patch-level heatmaps
- Natural language explanations
- Forensic contribution percentages
- Fusion weight explanations
- Visual evidence highlighting
"""

import numpy as np
import cv2
from typing import Dict, List, Optional, Tuple
from PIL import Image


class EnhancedExplainability:
    """
    Enhanced explainability engine for AI detection results.
    
    Provides detailed explanations of why an image was classified as
    AI-generated or authentic, including patch-level analysis and
    natural language descriptions.
    """
    
    def __init__(self):
        """Initialize enhanced explainability engine."""
        pass
    
    def extract_top_suspicious_patches(
        self,
        patch_probabilities: List[float],
        patch_locations: List[Tuple[int, int]],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Extract the top-k most suspicious patches.
        
        Args:
            patch_probabilities: List of AI probabilities for each patch
            patch_locations: List of (row, col) for each patch
            top_k: Number of top patches to return
            
        Returns:
            List of dictionaries containing patch information
        """
        if not patch_probabilities:
            return []
        
        # Sort patches by probability (descending)
        sorted_indices = np.argsort(patch_probabilities)[::-1]
        
        # Extract top-k
        top_patches = []
        for i in range(min(top_k, len(sorted_indices))):
            idx = sorted_indices[i]
            top_patches.append({
                'rank': i + 1,
                'probability': float(patch_probabilities[idx]),
                'location': patch_locations[idx],
                'row': patch_locations[idx][0],
                'col': patch_locations[idx][1]
            })
        
        return top_patches
    
    def generate_patch_heatmap(
        self,
        image_shape: Tuple[int, int],
        patch_probabilities: List[float],
        patch_locations: List[Tuple[int, int]],
        patch_size: int = 256
    ) -> np.ndarray:
        """
        Generate a heatmap visualization of patch-level AI probabilities.
        
        Args:
            image_shape: Shape of original image (h, w)
            patch_probabilities: List of AI probabilities for each patch
            patch_locations: List of (row, col) for each patch
            patch_size: Size of each patch
            
        Returns:
            Heatmap as numpy array (h, w, 3) in RGB format
        """
        h, w = image_shape
        heatmap = np.zeros((h, w), dtype=np.float32)
        count_map = np.zeros((h, w), dtype=np.float32)
        
        # Accumulate patch probabilities
        for prob, (row, col) in zip(patch_probabilities, patch_locations):
            # Add probability to patch region
            row_end = min(row + patch_size, h)
            col_end = min(col + patch_size, w)
            heatmap[row:row_end, col:col_end] += prob
            count_map[row:row_end, col:col_end] += 1
        
        # Average overlapping regions
        count_map[count_map == 0] = 1
        heatmap = heatmap / count_map
        
        # Normalize to [0, 255]
        heatmap = (heatmap * 255).astype(np.uint8)
        
        # Apply colormap (blue = low prob, red = high prob)
        heatmap_colored = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        return heatmap_colored
    
    def explain_forensic_contributions(
        self,
        forensic_contributions: Dict[str, float],
        image_type: str = "default"
    ) -> Dict:
        """
        Explain forensic module contributions in natural language.
        
        Args:
            forensic_contributions: Dictionary of forensic module scores
            image_type: Type of image for adaptive explanations
            
        Returns:
            Dictionary containing explanations for each module
        """
        explanations = {}
        
        # ELA explanation
        ela_score = forensic_contributions.get('ela', 0.0)
        if ela_score > 0.6:
            explanations['ela'] = {
                'score': ela_score,
                'finding': "Strong compression artifacts detected",
                'explanation': "Error Level Analysis reveals abnormal compression patterns "
                             "inconsistent with single-pass camera JPEG compression."
            }
        elif ela_score > 0.3:
            explanations['ela'] = {
                'score': ela_score,
                'finding': "Moderate compression artifacts",
                'explanation': "Some compression inconsistencies detected, possibly "
                             "from multiple save operations or AI generation."
            }
        else:
            explanations['ela'] = {
                'score': ela_score,
                'finding': "Normal compression levels",
                'explanation': "Compression artifacts are consistent with standard "
                             "camera JPEG compression."
            }
        
        # Noise explanation
        noise_score = forensic_contributions.get('noise', 0.0)
        if noise_score > 0.6:
            explanations['noise'] = {
                'score': noise_score,
                'finding': "Inconsistent sensor noise",
                'explanation': "Noise patterns vary significantly across image regions, "
                             "indicating possible splicing or AI generation."
            }
        elif noise_score > 0.3:
            explanations['noise'] = {
                'score': noise_score,
                'finding': "Moderate noise inconsistency",
                'explanation': "Some variation in noise patterns detected, may indicate "
                             "localized editing or AI smoothing."
            }
        else:
            explanations['noise'] = {
                'score': noise_score,
                'finding': "Consistent sensor noise",
                'explanation': "Sensor noise is uniform across the image, consistent with "
                             "authentic camera capture."
            }
        
        # Frequency explanation
        freq_score = forensic_contributions.get('frequency', 0.0)
        if freq_score > 0.6:
            explanations['frequency'] = {
                'score': freq_score,
                'finding': "Anomalous frequency spectrum",
                'explanation': "Frequency domain analysis reveals unnatural spectral "
                             "signatures characteristic of AI generation."
            }
        elif freq_score > 0.3:
            explanations['frequency'] = {
                'score': freq_score,
                'finding': "Unusual frequency patterns",
                'explanation': "Some frequency anomalies detected, possibly from AI "
                             "upscaling or generation artifacts."
            }
        else:
            explanations['frequency'] = {
                'score': freq_score,
                'finding': "Natural frequency spectrum",
                'explanation': "Frequency distribution is within natural camera range."
            }
        
        # Texture explanation
        texture_score = forensic_contributions.get('texture', 0.0)
        if texture_score > 0.6:
            explanations['texture'] = {
                'score': texture_score,
                'finding': "Over-smoothed texture",
                'explanation': "Texture uniformity suggests AI generation with "
                             "characteristic GAN/diffusion over-smoothing."
            }
        elif texture_score > 0.3:
            explanations['texture'] = {
                'score': texture_score,
                'finding': "Unusual texture patterns",
                'explanation': "Texture analysis reveals some anomalies possibly "
                             "from AI processing."
            }
        else:
            explanations['texture'] = {
                'score': texture_score,
                'finding': "Natural texture variation",
                'explanation': "Texture patterns are consistent with natural "
                             "camera imagery."
            }
        
        # Edge explanation
        edge_score = forensic_contributions.get('edge', 0.0)
        if edge_score > 0.5:
            explanations['edge'] = {
                'score': edge_score,
                'finding': "Unnatural edge patterns",
                'explanation': "Edge analysis reveals patterns characteristic of "
                             "AI-generated images."
            }
        else:
            explanations['edge'] = {
                'score': edge_score,
                'finding': "Natural edge consistency",
                'explanation': "Edge patterns are consistent with authentic imagery."
            }
        
        # Color explanation
        color_score = forensic_contributions.get('color', 0.0)
        if color_score > 0.4:
            explanations['color'] = {
                'score': color_score,
                'finding': "Color channel anomalies",
                'explanation': "Color channel analysis reveals anomalies possibly "
                             "from AI processing."
            }
        else:
            explanations['color'] = {
                'score': color_score,
                'finding': "Normal color distribution",
                'explanation': "Color channels are within natural ranges."
            }
        
        # EXIF explanation
        exif_score = forensic_contributions.get('exif', 0.0)
        if exif_score > 0.5:
            explanations['exif'] = {
                'score': exif_score,
                'finding': "Missing or inconsistent metadata",
                'explanation': "EXIF metadata is missing or inconsistent with "
                             "authentic camera capture."
            }
        else:
            explanations['exif'] = {
                'score': exif_score,
                'finding': "Consistent metadata",
                'explanation': "EXIF metadata is consistent with authentic camera capture."
            }
        
        return explanations
    
    def explain_fusion_weights(
        self,
        fusion_weights: Dict[str, float],
        image_type: str,
        has_faces: bool
    ) -> str:
        """
        Generate natural language explanation of fusion weights.
        
        Args:
            fusion_weights: Dictionary of fusion weights
            image_type: Type of image
            has_faces: Whether faces were detected
            
        Returns:
            Natural language explanation
        """
        explanations = []
        
        # Explain whole-image weight
        whole_image_weight = fusion_weights.get('whole_image', 0.0)
        if whole_image_weight > 0.4:
            explanations.append(
                f"Whole-image analysis ({whole_image_weight:.0%}) heavily influences "
                f"the decision, indicating the importance of global AI patterns."
            )
        
        # Explain face weight
        face_weight = fusion_weights.get('face', 0.0)
        if face_weight > 0.3:
            if has_faces:
                explanations.append(
                    f"Face analysis ({face_weight:.0%}) is prioritized due to "
                    f"detected faces, focusing on deepfake detection."
                )
            else:
                explanations.append(
                    f"Face analysis ({face_weight:.0%}) is included in the pipeline "
                    f"though no faces were detected."
                )
        
        # Explain forensic weight
        forensic_weight = fusion_weights.get('forensic', 0.0)
        if forensic_weight > 0.3:
            explanations.append(
                f"Forensic analysis ({forensic_weight:.0%}) plays a major role, "
                f"leveraging technical artifacts for detection."
            )
        
        # Explain CLIP weight
        clip_weight = fusion_weights.get('clip', 0.0)
        if clip_weight > 0.1:
            explanations.append(
                f"CLIP semantic analysis ({clip_weight:.0%}) contributes by "
                f"analyzing image content and AI generation patterns."
            )
        
        # Image type context
        if image_type == 'portrait':
            explanations.append(
                "Portrait pipeline prioritizes face analysis while maintaining "
                "forensic checks for comprehensive detection."
            )
        elif image_type == 'landscape':
            explanations.append(
                "Landscape pipeline balances whole-image and forensic analysis "
                "for robust detection of scenic AI content."
            )
        elif image_type == 'artwork':
            explanations.append(
                "Artwork pipeline emphasizes forensic analysis to detect "
                "AI-generated artistic content."
            )
        elif image_type == 'document':
            explanations.append(
                "Document pipeline focuses on forensic analysis to detect "
                "manipulated or AI-generated documents."
            )
        
        return " ".join(explanations)
    
    def generate_natural_language_explanation(
        self,
        verdict: str,
        confidence: float,
        ai_probability: float,
        forensic_contributions: Dict[str, float],
        patch_stats: Optional[Dict] = None,
        ood_score: Optional[float] = None,
        image_type: str = "default"
    ) -> Dict:
        """
        Generate comprehensive natural language explanation.
        
        Args:
            verdict: Final verdict
            confidence: Confidence score
            ai_probability: AI probability
            forensic_contributions: Forensic module scores
            patch_stats: Optional patch statistics
            ood_score: Optional OOD score
            image_type: Type of image
            
        Returns:
            Dictionary containing natural language explanations
        """
        # Verdict explanation
        if verdict == "AI Generated":
            verdict_explanation = (
                f"The image is classified as AI-generated with {confidence:.0%} confidence. "
                f"Multiple indicators suggest artificial origin, including "
                f"patterns consistent with modern AI image generators."
            )
        elif verdict == "Deepfake":
            verdict_explanation = (
                f"The image is classified as a deepfake with {confidence:.0%} confidence. "
                f"Face analysis reveals manipulation patterns indicative of "
                f"face-swapping or identity synthesis."
            )
        elif verdict == "Suspicious":
            verdict_explanation = (
                f"The image shows suspicious characteristics with {confidence:.0%} confidence. "
                f"Some indicators suggest possible AI generation or manipulation, "
                f"but the evidence is not conclusive."
            )
        elif verdict == "Likely Authentic":
            verdict_explanation = (
                f"The image is likely authentic with {confidence:.0%} confidence. "
                f"Most indicators are consistent with genuine camera capture, "
                f"though minor anomalies are present."
            )
        elif verdict == "Unknown Generation Method":
            verdict_explanation = (
                f"The image's generation method cannot be confidently determined. "
                f"The image exhibits characteristics outside the known distribution "
                f"of both authentic and AI-generated samples."
            )
        else:  # Authentic
            verdict_explanation = (
                f"The image is classified as authentic with {confidence:.0%} confidence. "
                f"All technical indicators are consistent with genuine camera capture."
            )
        
        # AI probability explanation
        ai_prob_explanation = (
            f"The estimated probability of AI generation is {ai_probability:.1f}%. "
            f"This probability is derived from a weighted fusion of multiple "
            f"detection modules."
        )
        
        # Forensic summary
        forensic_explanations = self.explain_forensic_contributions(
            forensic_contributions, image_type
        )
        
        # Identify key findings
        key_findings = []
        for module, explanation in forensic_explanations.items():
            if explanation['score'] > 0.5:
                key_findings.append(explanation['finding'])
        
        # Patch analysis explanation
        patch_explanation = ""
        if patch_stats:
            num_patches = patch_stats.get('number_of_patches', 0)
            highest_prob = patch_stats.get('highest_patch_probability', 0.0)
            avg_prob = patch_stats.get('average_patch_probability', 0.0)
            
            if num_patches > 0:
                patch_explanation = (
                    f"Patch-based analysis examined {num_patches} image regions. "
                    f"The most suspicious region shows {highest_prob:.1%} AI probability, "
                    f"while the average across all patches is {avg_prob:.1%}. "
                )
                
                if highest_prob > 0.8:
                    patch_explanation += "Localized regions show strong AI generation patterns."
                elif highest_prob > 0.5:
                    patch_explanation += "Some regions exhibit AI-like characteristics."
                else:
                    patch_explanation += "Patch analysis does not reveal strong AI indicators."
        
        # OOD explanation
        ood_explanation = ""
        if ood_score is not None:
            if ood_score > 0.7:
                ood_explanation = (
                    f"The image exhibits characteristics outside the known distribution "
                    f"(OOD score: {ood_score:.2f}), increasing uncertainty in the prediction."
                )
            elif ood_score > 0.4:
                ood_explanation = (
                    f"The image shows some out-of-distribution characteristics "
                    f"(OOD score: {ood_score:.2f}), suggesting unusual content."
                )
            else:
                ood_explanation = (
                    f"The image falls within the known distribution "
                    f"(OOD score: {ood_score:.2f}), supporting the confidence of the prediction."
                )
        
        return {
            'verdict_explanation': verdict_explanation,
            'ai_probability_explanation': ai_prob_explanation,
            'forensic_explanations': forensic_explanations,
            'key_findings': key_findings,
            'patch_explanation': patch_explanation,
            'ood_explanation': ood_explanation
        }
    
    def generate_comprehensive_report(
        self,
        verdict: str,
        confidence: float,
        ai_probability: float,
        forensic_contributions: Dict[str, float],
        fusion_weights: Dict[str, float],
        patch_stats: Optional[Dict] = None,
        ood_score: Optional[float] = None,
        image_type: str = "default",
        has_faces: bool = False
    ) -> Dict:
        """
        Generate a comprehensive explainability report.
        
        Args:
            verdict: Final verdict
            confidence: Confidence score
            ai_probability: AI probability
            forensic_contributions: Forensic module scores
            fusion_weights: Fusion weights used
            patch_stats: Optional patch statistics
            ood_score: Optional OOD score
            image_type: Type of image
            has_faces: Whether faces were detected
            
        Returns:
            Comprehensive explainability report
        """
        # Top suspicious patches
        top_patches = []
        if patch_stats:
            top_patches = self.extract_top_suspicious_patches(
                patch_stats.get('patch_probabilities', []),
                patch_stats.get('patch_locations', []),
                top_k=5
            )
        
        # Natural language explanations
        nl_explanations = self.generate_natural_language_explanation(
            verdict, confidence, ai_probability, forensic_contributions,
            patch_stats, ood_score, image_type
        )
        
        # Fusion weight explanation
        fusion_explanation = self.explain_fusion_weights(
            fusion_weights, image_type, has_faces
        )
        
        # Forensic contribution percentages
        total_forensic = sum(forensic_contributions.values())
        forensic_percentages = {
            k: (v / total_forensic * 100) if total_forensic > 0 else 0
            for k, v in forensic_contributions.items()
        }
        
        return {
            'verdict': verdict,
            'confidence': confidence,
            'ai_probability': ai_probability,
            'top_suspicious_patches': top_patches,
            'natural_language_explanations': nl_explanations,
            'fusion_weight_explanation': fusion_explanation,
            'forensic_contribution_percentages': forensic_percentages,
            'ood_score': ood_score,
            'image_type': image_type,
            'patch_statistics': patch_stats
        }


# Global explainability instance
_explainability = None


def get_explainability() -> EnhancedExplainability:
    """
    Get or create the global explainability instance.
    
    Returns:
        EnhancedExplainability instance
    """
    global _explainability
    if _explainability is None:
        _explainability = EnhancedExplainability()
    return _explainability


def generate_explainability_report(
    verdict: str,
    confidence: float,
    ai_probability: float,
    forensic_contributions: Dict[str, float],
    fusion_weights: Dict[str, float],
    patch_stats: Optional[Dict] = None,
    ood_score: Optional[float] = None,
    image_type: str = "default",
    has_faces: bool = False
) -> Dict:
    """
    Convenience function for generating explainability reports.
    
    Args:
        verdict: Final verdict
        confidence: Confidence score
        ai_probability: AI probability
        forensic_contributions: Forensic module scores
        fusion_weights: Fusion weights used
        patch_stats: Optional patch statistics
        ood_score: Optional OOD score
        image_type: Type of image
        has_faces: Whether faces were detected
        
    Returns:
        Comprehensive explainability report
    """
    explainability = get_explainability()
    return explainability.generate_comprehensive_report(
        verdict, confidence, ai_probability, forensic_contributions,
        fusion_weights, patch_stats, ood_score, image_type, has_faces
    )

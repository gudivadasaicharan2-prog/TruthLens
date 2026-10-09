"""
Diffusion Fingerprint Heuristics - TruthLens v2.3

Lightweight heuristics for detecting diffusion-generated images without training.
Implements multiple artifact detection methods specific to diffusion models.

Key features:
- Texture repetition detection
- Over-smooth gradient analysis
- Diffusion denoising residual detection
- Color consistency analysis
- Local entropy analysis
- Edge smoothness detection
- Frequency ring artifact detection
"""

import cv2
import numpy as np
from typing import Dict, Tuple
from scipy import ndimage
from scipy.fft import fft2, fftshift


class DiffusionFingerprint:
    """
    Diffusion fingerprint detector for identifying diffusion-generated images.
    
    Uses multiple lightweight heuristics to detect artifacts common in
    diffusion model outputs without requiring model training.
    """
    
    def __init__(self):
        """Initialize diffusion fingerprint detector."""
        pass
    
    def analyze(self, img_array: np.ndarray, gray: np.ndarray) -> Dict:
        """
        Run all diffusion fingerprint heuristics.
        
        Args:
            img_array: RGB image as numpy array (H, W, 3)
            gray: Grayscale image as numpy array (H, W)
            
        Returns:
            Dictionary containing:
                - diffusion_fingerprint_score: Overall score [0, 1]
                - individual heuristic scores
                - details about each heuristic
        """
        scores = {}
        
        # Run individual heuristics
        scores['texture_repetition'] = self._detect_texture_repetition(gray)
        scores['smooth_gradients'] = self._detect_smooth_gradients(gray)
        scores['denoising_residual'] = self._detect_denoising_residual(gray)
        scores['color_consistency'] = self._detect_color_consistency(img_array)
        scores['local_entropy'] = self._detect_local_entropy(gray)
        scores['edge_smoothness'] = self._detect_edge_smoothness(gray)
        scores['frequency_rings'] = self._detect_frequency_rings(gray)
        
        # Calculate overall score (weighted average)
        weights = {
            'texture_repetition': 0.15,
            'smooth_gradients': 0.15,
            'denoising_residual': 0.20,
            'color_consistency': 0.10,
            'local_entropy': 0.15,
            'edge_smoothness': 0.15,
            'frequency_rings': 0.10
        }
        
        overall_score = sum(scores[k] * weights[k] for k in scores.keys())
        
        return {
            'diffusion_fingerprint_score': float(overall_score),
            'heuristic_scores': {k: float(v) for k, v in scores.items()},
            'weights': weights
        }
    
    def _detect_texture_repetition(self, gray: np.ndarray) -> float:
        """
        Detect texture repetition patterns common in diffusion outputs.
        
        Diffusion models often create repeating texture patterns due to
        attention mechanism artifacts.
        
        Args:
            gray: Grayscale image
            
        Returns:
            Score [0, 1] where higher indicates more repetition
        """
        try:
            # Calculate local binary patterns
            h, w = gray.shape
            
            # Use autocorrelation to detect repeating patterns
            # Compute FFT
            f = fft2(gray)
            fshift = fftshift(f)
            magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1)
            
            # Look for peaks in frequency domain (indicates repetition)
            rows, cols = gray.shape
            crow, ccol = rows // 2, cols // 2
            
            # Extract high-frequency regions
            mask = np.zeros((rows, cols), np.uint8)
            mask[crow-30:crow+30, ccol-30:ccol+30] = 255
            
            # Count peaks
            peaks = cv2.countNonZero(cv2.inRange(magnitude_spectrum, 0, 255))
            
            # Normalize score
            repetition_score = min(peaks / 1000.0, 1.0)
            
            return repetition_score
            
        except Exception:
            return 0.0
    
    def _detect_smooth_gradients(self, gray: np.ndarray) -> float:
        """
        Detect over-smooth gradients common in diffusion outputs.
        
        Diffusion models tend to produce overly smooth gradient transitions
        compared to natural images.
        
        Args:
            gray: Grayscale image
            
        Returns:
            Score [0, 1] where higher indicates smoother gradients
        """
        try:
            # Calculate gradient magnitude
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # Calculate gradient smoothness (variance of gradient)
            grad_var = np.var(gradient_magnitude)
            
            # Natural images have higher gradient variance
            # Diffusion outputs tend to have lower variance
            smooth_score = 1.0 - min(grad_var / 1000.0, 1.0)
            
            return smooth_score
            
        except Exception:
            return 0.0
    
    def _detect_denoising_residual(self, gray: np.ndarray) -> float:
        """
        Detect diffusion denoising residual artifacts.
        
        Diffusion models leave characteristic residual patterns from
        the denoising process.
        
        Args:
            gray: Grayscale image
            
        Returns:
            Score [0, 1] where higher indicates more residual artifacts
        """
        try:
            # Apply Gaussian blur to simulate denoising
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Calculate residual (difference between original and blurred)
            residual = cv2.absdiff(gray, blurred)
            
            # Analyze residual patterns
            residual_mean = np.mean(residual)
            residual_std = np.std(residual)
            
            # High residual with low std indicates diffusion artifacts
            residual_score = min((residual_mean / (residual_std + 1e-6)) / 10.0, 1.0)
            
            return residual_score
            
        except Exception:
            return 0.0
    
    def _detect_color_consistency(self, img_array: np.ndarray) -> float:
        """
        Detect overly consistent color distributions.
        
        Diffusion models often produce images with unnaturally
        consistent color distributions.
        
        Args:
            img_array: RGB image
            
        Returns:
            Score [0, 1] where higher indicates more consistent colors
        """
        try:
            # Calculate color histograms for each channel
            color_scores = []
            
            for channel in range(3):
                hist = cv2.calcHist([img_array], [channel], None, [256], [0, 256])
                hist = hist / hist.sum()  # Normalize
                
                # Calculate histogram uniformity
                hist_std = np.std(hist)
                color_scores.append(1.0 - min(hist_std / 0.1, 1.0))
            
            # Average across channels
            color_score = np.mean(color_scores)
            
            return color_score
            
        except Exception:
            return 0.0
    
    def _detect_local_entropy(self, gray: np.ndarray) -> float:
        """
        Detect local entropy patterns.
        
        Diffusion outputs often have uniform local entropy
        compared to natural images.
        
        Args:
            gray: Grayscale image
            
        Returns:
            Score [0, 1] where higher indicates more uniform entropy
        """
        try:
            # Calculate local entropy using sliding window
            h, w = gray.shape
            window_size = 16
            stride = 8
            
            entropies = []
            
            for i in range(0, h - window_size, stride):
                for j in range(0, w - window_size, stride):
                    window = gray[i:i+window_size, j:j+window_size]
                    
                    # Calculate histogram
                    hist = cv2.calcHist([window], [0], None, [256], [0, 256])
                    hist = hist / hist.sum()
                    
                    # Calculate entropy
                    entropy = -np.sum(hist * np.log2(hist + 1e-10))
                    entropies.append(entropy)
            
            if not entropies:
                return 0.0
            
            # Calculate entropy variance
            entropy_var = np.var(entropies)
            
            # Low variance indicates uniform entropy (diffusion artifact)
            entropy_score = 1.0 - min(entropy_var / 2.0, 1.0)
            
            return entropy_score
            
        except Exception:
            return 0.0
    
    def _detect_edge_smoothness(self, gray: np.ndarray) -> float:
        """
        Detect overly smooth edges.
        
        Diffusion models tend to produce smoother edges than natural images.
        
        Args:
            gray: Grayscale image
            
        Returns:
            Score [0, 1] where higher indicates smoother edges
        """
        try:
            # Detect edges using Canny
            edges = cv2.Canny(gray, 50, 150)
            
            # Calculate edge statistics
            edge_count = np.sum(edges > 0)
            total_pixels = edges.size
            edge_density = edge_count / total_pixels
            
            # Calculate edge strength variance
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edge_strength = np.sqrt(sobel_x**2 + sobel_y**2)
            edge_strength_var = np.var(edge_strength[edges > 0]) if edge_count > 0 else 0
            
            # Combine edge density and strength variance
            # Low density + low variance = smooth edges (diffusion artifact)
            smooth_score = (1.0 - min(edge_density / 0.1, 1.0)) * 0.5 + \
                          (1.0 - min(edge_strength_var / 100.0, 1.0)) * 0.5
            
            return smooth_score
            
        except Exception:
            return 0.0
    
    def _detect_frequency_rings(self, gray: np.ndarray) -> float:
        """
        Detect frequency ring artifacts in FFT domain.
        
        Diffusion models can produce characteristic ring patterns
        in the frequency domain.
        
        Args:
            gray: Grayscale image
            
        Returns:
            Score [0, 1] where higher indicates more ring artifacts
        """
        try:
            # Compute FFT
            f = fft2(gray)
            fshift = fftshift(f)
            magnitude_spectrum = np.abs(fshift)
            
            # Convert to log scale
            log_spectrum = 20 * np.log(magnitude_spectrum + 1)
            
            # Detect circular patterns
            h, w = log_spectrum.shape
            center = (h // 2, w // 2)
            
            # Create radial profile
            y, x = np.ogrid[:h, :w]
            radius_map = np.sqrt((x - center[1])**2 + (y - center[0])**2)
            
            # Sample values at different radii
            radii = np.arange(1, min(h, w) // 2, 5)
            radial_values = []
            
            for r in radii:
                mask = (radius_map >= r) & (radius_map < r + 5)
                if np.any(mask):
                    radial_values.append(np.mean(log_spectrum[mask]))
            
            if not radial_values:
                return 0.0
            
            # Calculate variance in radial profile
            # Ring artifacts cause periodic variations
            radial_var = np.var(radial_values)
            
            # High radial variance indicates ring artifacts
            ring_score = min(radial_var / 50.0, 1.0)
            
            return ring_score
            
        except Exception:
            return 0.0


def diffusion_fingerprint_score(
    img_array: np.ndarray,
    gray: np.ndarray
) -> float:
    """
    Convenience function to calculate diffusion fingerprint score.
    
    Args:
        img_array: RGB image as numpy array
        gray: Grayscale image as numpy array
        
    Returns:
        Diffusion fingerprint score [0, 1]
    """
    detector = DiffusionFingerprint()
    result = detector.analyze(img_array, gray)
    return result['diffusion_fingerprint_score']


def diffusion_fingerprint_analysis(
    img_array: np.ndarray,
    gray: np.ndarray
) -> Dict:
    """
    Convenience function for full diffusion fingerprint analysis.
    
    Args:
        img_array: RGB image as numpy array
        gray: Grayscale image as numpy array
        
    Returns:
        Dictionary containing full analysis results
    """
    detector = DiffusionFingerprint()
    return detector.analyze(img_array, gray)

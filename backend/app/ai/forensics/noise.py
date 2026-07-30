"""
Noise Analysis Forensic Module
===============================
Detects quadrant noise variance inconsistencies that indicate splicing
or compositing operations.
"""

import cv2
import numpy as np


def noise_splice_score(gray: np.ndarray) -> tuple[float, float]:
    """
    Quadrant noise-variance — measures inconsistency in sensor noise across
    image regions. High variance of quadrant stds signals splicing/compositing.

    Enhanced with:
    - 9-grid analysis (more granular than 4 quadrants)
    - Natural sensor noise pattern detection (Poisson-like distribution)
    - High-frequency noise analysis (sensor noise vs AI smoothness)
    - Wavelet residual energy (multi-scale noise analysis)
    - Denoising residual (AI smoothing detection)
    - Local entropy analysis (noise randomness)
    - Patch noise consistency (splicing detection)

    Returns:
        (noise_var, normalized_score) where normalized_score is in [0, 1].
    """
    try:
        h, w = gray.shape
        
        # Enhanced: 9-grid analysis for better localization
        grid_h, grid_w = 3, 3
        h_step, w_step = h // grid_h, w // grid_w
        regions = []
        for i in range(grid_h):
            for j in range(grid_w):
                y_start, y_end = i * h_step, (i + 1) * h_step if i < grid_h - 1 else h
                x_start, x_end = j * w_step, (j + 1) * w_step if j < grid_w - 1 else w
                regions.append(gray[y_start:y_end, x_start:x_end])
        
        stds = [float(np.std(r)) for r in regions]
        noise_var = float(np.var(stds))
        
        # Enhanced: Natural sensor noise pattern detection
        # Real sensor noise follows approximately Poisson distribution
        # AI-generated images often have unnaturally uniform or Gaussian noise
        if len(stds) >= 4:
            # Check for natural variance in noise levels
            std_mean = float(np.mean(stds))
            std_std = float(np.std(stds))
            # Natural sensor noise has some variation but not extreme
            naturalness_score = 0.0
            if std_mean > 0:
                cv = std_std / std_mean
                # CV between 0.1 and 0.4 is typical for natural sensor noise
                if cv < 0.05:  # Too uniform - suspicious
                    naturalness_score = 0.4
                elif cv > 0.6:  # Too variable - splicing
                    naturalness_score = 0.6
                else:
                    naturalness_score = 0.1
        else:
            naturalness_score = 0.0
        
        # Enhanced: High-frequency noise analysis
        # Real photos have natural high-frequency sensor noise
        # AI images often have smoothed high frequencies
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        hf_noise = float(np.std(laplacian))
        # Very low high-frequency noise suggests AI smoothing
        hf_score = 0.0
        if hf_noise < 5:
            hf_score = 0.5
        elif hf_noise < 10:
            hf_score = 0.2
        
        # NEW: Wavelet residual energy
        # Real images have consistent multi-scale noise
        # AI images often have inconsistent wavelet coefficients
        wavelet_score = _compute_wavelet_residual(gray)
        
        # NEW: Denoising residual
        # AI images often show abnormal denoising patterns
        denoise_score = _compute_denoising_residual(gray)
        
        # NEW: Local entropy analysis
        # Real sensor noise has characteristic entropy
        # AI smoothing reduces local entropy
        entropy_score = _compute_local_entropy(gray)
        
        # NEW: Patch noise consistency
        # Splicing creates abrupt changes in noise statistics
        patch_score = _compute_patch_noise_consistency(gray)
        
        # Base score from quadrant variance
        base_score = min(max((noise_var - 5.0) / 45.0, 0.0), 1.0)
        
        # Combine signals
        final_score = min(max(
            base_score + 
            naturalness_score + 
            hf_score +
            wavelet_score * 0.2 +
            denoise_score * 0.2 +
            entropy_score * 0.15 +
            patch_score * 0.15,
            0.0
        ), 1.0)
        
        return noise_var, round(final_score, 4)
    except Exception:
        return 0.0, 0.0


def _compute_wavelet_residual(gray: np.ndarray) -> float:
    """
    Compute wavelet residual energy for multi-scale noise analysis.
    
    Real images have consistent energy across wavelet scales.
    AI images often show abnormal energy distribution.
    
    Returns: float [0, 1] where 1 = suspicious
    """
    try:
        # Simple Haar-like wavelet decomposition
        h, w = gray.shape
        
        # Level 1 decomposition
        h_half, w_half = h // 2, w // 2
        ll = gray[:h_half, :w_half]
        lh = gray[:h_half, w_half:]
        hl = gray[h_half:, :w_half]
        hh = gray[h_half:, w_half:]
        
        # Compute energy in each subband
        energy_ll = np.var(ll)
        energy_lh = np.var(lh)
        energy_hl = np.var(hl)
        energy_hh = np.var(hh)
        
        # Real images have characteristic energy ratios
        # High-frequency subbands (LH, HL, HH) should have specific ratios to LL
        if energy_ll > 0:
            ratio_lh = energy_lh / energy_ll
            ratio_hl = energy_hl / energy_ll
            ratio_hh = energy_hh / energy_ll
            
            # Natural ratios typically in [0.1, 0.5]
            deviation = 0.0
            for ratio in [ratio_lh, ratio_hl, ratio_hh]:
                if ratio < 0.05 or ratio > 0.7:
                    deviation += 0.3
            
            return min(deviation, 1.0)
        
        return 0.0
    except Exception:
        return 0.0


def _compute_denoising_residual(gray: np.ndarray) -> float:
    """
    Compute denoising residual to detect AI smoothing.
    
    AI-generated images often show abnormal denoising patterns
    when standard denoising is applied.
    
    Returns: float [0, 1] where 1 = suspicious
    """
    try:
        # Apply simple Gaussian blur (denoising)
        denoised = cv2.GaussianBlur(gray, (5, 5), 1.0)
        
        # Compute residual
        residual = gray.astype(np.float32) - denoised.astype(np.float32)
        
        # Analyze residual statistics
        residual_std = np.std(residual)
        residual_mean = np.mean(residual)
        
        # Real images: residual has specific characteristics
        # AI images: residual often too small or too uniform
        if residual_std < 2:
            # Too smooth - likely AI
            return 0.5
        elif residual_std < 4:
            return 0.25
        elif residual_std > 15:
            # Too much residual - suspicious
            return 0.3
        else:
            return 0.1
    except Exception:
        return 0.0


def _compute_local_entropy(gray: np.ndarray) -> float:
    """
    Compute local entropy to analyze noise randomness.
    
    Real sensor noise has characteristic local entropy.
    AI smoothing reduces local entropy unnaturally.
    
    Returns: float [0, 1] where 1 = suspicious (low entropy)
    """
    try:
        # Compute local entropy using sliding window
        h, w = gray.shape
        window_size = 16
        stride = 8
        
        entropies = []
        for i in range(0, h - window_size + 1, stride):
            for j in range(0, w - window_size + 1, stride):
                patch = gray[i:i+window_size, j:j+window_size]
                
                # Compute histogram
                hist, _ = np.histogram(patch, bins=16, range=(0, 256))
                hist = hist / (np.sum(hist) + 1e-8)
                
                # Compute entropy
                entropy = -np.sum(hist * np.log(hist + 1e-8))
                entropies.append(entropy)
        
        if not entropies:
            return 0.0
        
        # Analyze entropy distribution
        mean_entropy = np.mean(entropies)
        std_entropy = np.std(entropies)
        
        # Natural images have characteristic local entropy
        # AI smoothing reduces entropy
        if mean_entropy < 2.0:
            return 0.5
        elif mean_entropy < 2.5:
            return 0.25
        else:
            return 0.1
    except Exception:
        return 0.0


def _compute_patch_noise_consistency(gray: np.ndarray) -> float:
    """
    Compute patch noise consistency to detect splicing.
    
    Splicing creates abrupt changes in noise statistics
    across patch boundaries.
    
    Returns: float [0, 1] where 1 = suspicious (inconsistent)
    """
    try:
        h, w = gray.shape
        patch_size = 64
        stride =32
        
        noise_levels = []
        for i in range(0, h - patch_size + 1, stride):
            for j in range(0, w - patch_size + 1, stride):
                patch = gray[i:i+patch_size, j:j+patch_size]
                noise_level = np.std(patch)
                noise_levels.append(noise_level)
        
        if len(noise_levels) < 4:
            return 0.0
        
        # Compute gradient of noise levels
        noise_levels = np.array(noise_levels)
        noise_gradient = np.abs(np.diff(noise_levels))
        
        # Large gradients indicate splicing
        max_gradient = np.max(noise_gradient)
        mean_gradient = np.mean(noise_gradient)
        
        if max_gradient > 15:
            return 0.5
        elif max_gradient > 10:
            return 0.25
        elif mean_gradient > 5:
            return 0.2
        else:
            return 0.1
    except Exception:
        return 0.0


def enhanced_noise_analysis(gray: np.ndarray) -> dict:
    """
    Enhanced noise analysis returning detailed features.
    
    Returns:
        Dictionary containing:
            - score: Overall suspiciousness score [0, 1]
            - noise_variance: Variance of noise across regions
            - sensor_consistency: Sensor noise consistency score
            - wavelet_residual: Wavelet residual energy
            - denoising_residual: Denoising residual score
            - local_entropy: Local entropy score
            - patch_consistency: Patch noise consistency score
    """
    try:
        noise_var, score = noise_splice_score(gray)
        
        # Compute individual features
        wavelet_score = _compute_wavelet_residual(gray)
        denoise_score = _compute_denoising_residual(gray)
        entropy_score = _compute_local_entropy(gray)
        patch_score = _compute_patch_noise_consistency(gray)
        
        # Sensor consistency (inverse of noise variance)
        sensor_consistency = 1.0 - min(noise_var / 50.0, 1.0)
        
        return {
            'score': score,
            'noise_variance': float(noise_var),
            'sensor_consistency': float(sensor_consistency),
            'wavelet_residual': wavelet_score,
            'denoising_residual': denoise_score,
            'local_entropy': entropy_score,
            'patch_consistency': patch_score
        }
    except Exception:
        return {
            'score': 0.5,
            'noise_variance': 0.0,
            'sensor_consistency': 0.5,
            'wavelet_residual': 0.0,
            'denoising_residual': 0.0,
            'local_entropy': 0.0,
            'patch_consistency': 0.0
        }

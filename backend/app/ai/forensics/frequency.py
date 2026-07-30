"""
Frequency Domain Analysis Forensic Module
==========================================
Detects anomalous frequency spectra using 2D FFT analysis.
"""

import numpy as np


def frequency_domain_score(gray: np.ndarray) -> float:
    """
    Frequency-domain analysis via 2-D FFT.

    Real camera images have characteristic high-frequency energy (lens
    diffraction, sensor noise, natural texture detail).  AI-generated images
    often show anomalous frequency profiles — too clean or periodically
    structured (GAN grid artifacts, diffusion spectral signatures).

    Enhanced with:
    - Radial frequency analysis (natural falloff vs AI patterns)
    - High-frequency energy ratio (sensor noise vs AI smoothing)
    - Frequency entropy (natural randomness vs AI structure)
    - Spectral peak detection (periodic artifacts)
    - Ring artifact detection (GAN grid patterns)
    - Checkerboard artifact detection (upsampling artifacts)

    Returns: float [0, 1] where 1 = suspicious.
    """
    try:
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1)
        freq_mean = float(np.mean(magnitude))
        freq_std  = float(np.std(magnitude))

        # Mean outside natural range [75, 190] is suspicious
        mean_score = 0.0
        if freq_mean < 55 or freq_mean > 230:
            mean_score = 0.80
        elif freq_mean < 75 or freq_mean > 190:
            mean_score = 0.40

        # Very low std = unnaturally uniform frequency spectrum
        std_score = 0.0
        if freq_std < 15:
            std_score = 0.75
        elif freq_std < 25:
            std_score = 0.35
        
        # Enhanced: Radial frequency analysis
        # Natural images have characteristic 1/f falloff
        # AI images often have unnatural frequency distribution
        h, w = magnitude.shape
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        radius = np.sqrt((x - cx)**2 + (y - cy)**2)
        
        # Divide into radial bins
        max_radius = min(cx, cy)
        if max_radius > 10:
            bins = 10
            bin_edges = np.linspace(0, max_radius, bins + 1)
            radial_profile = []
            for i in range(bins):
                mask = (radius >= bin_edges[i]) & (radius < bin_edges[i + 1])
                if np.sum(mask) > 0:
                    radial_profile.append(np.mean(magnitude[mask]))
            
            if len(radial_profile) >= 5:
                # Check for natural falloff (decreasing with radius)
                # AI images often have flat or increasing profiles
                profile_diff = np.diff(radial_profile)
                # Natural: mostly negative differences (falloff)
                negative_ratio = np.sum(profile_diff < 0) / len(profile_diff)
                if negative_ratio < 0.3:  # Too flat or increasing
                    radial_score = 0.4
                else:
                    radial_score = 0.1
            else:
                radial_score = 0.0
        else:
            radial_score = 0.0
        
        # Enhanced: High-frequency energy ratio
        # Real photos have significant high-frequency energy
        # AI images often suppress high frequencies
        hf_mask = radius > (max_radius * 0.6)
        if np.sum(hf_mask) > 0:
            lf_energy = np.mean(magnitude[~hf_mask]) if np.sum(~hf_mask) > 0 else 0
            hf_energy = np.mean(magnitude[hf_mask])
            if lf_energy > 0:
                hf_ratio = hf_energy / lf_energy
                # Natural images have hf_ratio around 0.3-0.7
                if hf_ratio < 0.15:  # Too smooth
                    hf_score = 0.5
                elif hf_ratio < 0.25:
                    hf_score = 0.25
                else:
                    hf_score = 0.1
            else:
                hf_score = 0.0
        else:
            hf_score = 0.0
        
        # NEW: Frequency entropy
        # Natural images have higher entropy (more randomness)
        # AI images often have lower entropy (more structured)
        entropy_score = _compute_frequency_entropy(magnitude)
        
        # NEW: Spectral peak detection
        # Periodic artifacts create distinct peaks in frequency domain
        peak_score = _detect_spectral_peaks(magnitude)
        
        # NEW: Ring artifact detection
        # GAN grid artifacts create ring patterns in frequency domain
        ring_score = _detect_ring_artifacts(magnitude, cx, cy)
        
        # NEW: Checkerboard artifact detection
        # Upsampling artifacts create checkerboard patterns
        checkerboard_score = _detect_checkerboard_artifacts(magnitude)
        
        # Combine all signals
        base_score = (mean_score + std_score) / 2.0
        final_score = min(max(
            base_score + 
            radial_score * 0.2 + 
            hf_score * 0.2 +
            entropy_score * 0.15 +
            peak_score * 0.15 +
            ring_score * 0.15 +
            checkerboard_score * 0.15,
            0.0
        ), 1.0)
        
        return round(final_score, 4)
    except Exception:
        return 0.5


def _compute_frequency_entropy(magnitude: np.ndarray) -> float:
    """
    Compute entropy of frequency spectrum.
    
    Natural images have higher entropy (more random distribution)
    AI images often have lower entropy (more structured/periodic)
    
    Returns: float [0, 1] where 1 = suspicious (low entropy)
    """
    try:
        # Normalize magnitude to probability distribution
        mag_flat = magnitude.flatten()
        mag_flat = mag_flat - np.min(mag_flat)
        mag_flat = mag_flat / (np.sum(mag_flat) + 1e-8)
        
        # Compute entropy
        entropy = -np.sum(mag_flat * np.log(mag_flat + 1e-8))
        
        # Normalize by max possible entropy (log of number of bins)
        max_entropy = np.log(len(mag_flat))
        normalized_entropy = entropy / max_entropy
        
        # Low entropy = suspicious
        # Natural images typically have entropy > 0.7
        if normalized_entropy < 0.5:
            return 0.6
        elif normalized_entropy < 0.65:
            return 0.3
        else:
            return 0.1
    except Exception:
        return 0.0


def _detect_spectral_peaks(magnitude: np.ndarray) -> float:
    """
    Detect periodic artifacts through spectral peak analysis.
    
    Periodic artifacts (GAN grids, repeating patterns) create
    distinct peaks in the frequency domain.
    
    Returns: float [0, 1] where 1 = suspicious (many peaks)
    """
    try:
        h, w = magnitude.shape
        
        # Remove DC component (center)
        cy, cx = h // 2, w // 2
        magnitude_no_dc = magnitude.copy()
        magnitude_no_dc[cy-5:cy+5, cx-5:cx+5] = 0
        
        # Find local maxima
        from scipy.ndimage import maximum_filter
        
        # Local maximum filter
        neighborhood_size = 11
        local_max = maximum_filter(magnitude_no_dc, size=neighborhood_size)
        peaks = (magnitude_no_dc == local_max) & (magnitude_no_dc > np.mean(magnitude_no_dc))
        
        # Count peaks
        num_peaks = np.sum(peaks)
        
        # Normalize by image size
        peak_density = num_peaks / (h * w)
        
        # High peak density = suspicious
        if peak_density > 1e-4:
            return 0.5
        elif peak_density > 5e-5:
            return 0.25
        else:
            return 0.1
    except Exception:
        return 0.0


def _detect_ring_artifacts(magnitude: np.ndarray, cx: int, cy: int) -> float:
    """
    Detect ring artifacts characteristic of GAN grid patterns.
    
    GAN grid artifacts create concentric rings in frequency domain.
    
    Returns: float [0, 1] where 1 = suspicious (ring artifacts)
    """
    try:
        h, w = magnitude.shape
        y, x = np.ogrid[:h, :w]
        radius = np.sqrt((x - cx)**2 + (y - cy)**2)
        
        # Compute radial profile
        max_radius = min(cx, cy)
        if max_radius < 10:
            return 0.0
        
        bins = 20
        bin_edges = np.linspace(0, max_radius, bins + 1)
        radial_profile = []
        for i in range(bins):
            mask = (radius >= bin_edges[i]) & (radius < bin_edges[i + 1])
            if np.sum(mask) > 0:
                radial_profile.append(np.mean(magnitude[mask]))
        
        if len(radial_profile) < 10:
            return 0.0
        
        # Detect oscillations (rings create periodic peaks in radial profile)
        radial_profile = np.array(radial_profile)
        
        # Compute second derivative to detect oscillations
        second_deriv = np.diff(radial_profile, n=2)
        
        # Count sign changes (oscillations)
        sign_changes = np.sum(second_deriv[:-1] * second_deriv[1:] < 0)
        
        # Normalize by length
        oscillation_ratio = sign_changes / len(radial_profile)
        
        # High oscillation = ring artifacts
        if oscillation_ratio > 0.6:
            return 0.5
        elif oscillation_ratio > 0.4:
            return 0.25
        else:
            return 0.1
    except Exception:
        return 0.0


def _detect_checkerboard_artifacts(magnitude: np.ndarray) -> float:
    """
    Detect checkerboard artifacts from upsampling.
    
    Upsampling artifacts create checkerboard patterns in frequency domain
    (high energy at alternating positions).
    
    Returns: float [0, 1] where 1 = suspicious (checkerboard artifacts)
    """
    try:
        h, w = magnitude.shape
        
        # Sample alternating positions (checkerboard pattern)
        # This is characteristic of upsampling artifacts
        mask1 = np.zeros((h, w), dtype=bool)
        mask2 = np.zeros((h, w), dtype=bool)
        
        mask1[::2, ::2] = True
        mask1[1::2, 1::2] = True
        mask2[::2, 1::2] = True
        mask2[1::2, ::2] = True
        
        # Compute energy in alternating positions
        energy1 = np.mean(magnitude[mask1])
        energy2 = np.mean(magnitude[mask2])
        
        # Checkerboard artifacts create high energy difference
        energy_diff = abs(energy1 - energy2)
        total_energy = energy1 + energy2 + 1e-8
        
        # Normalize difference
        normalized_diff = energy_diff / total_energy
        
        # High difference = checkerboard artifacts
        if normalized_diff > 0.3:
            return 0.5
        elif normalized_diff > 0.2:
            return 0.25
        else:
            return 0.1
    except Exception:
        return 0.0


def enhanced_frequency_analysis(gray: np.ndarray) -> dict:
    """
    Enhanced frequency analysis returning detailed features.
    
    Returns:
        Dictionary containing:
            - score: Overall suspiciousness score [0, 1]
            - frequency_entropy: Entropy of frequency spectrum
            - spectral_peaks: Number of spectral peaks detected
            - ring_artifacts: Ring artifact score
            - checkerboard_artifacts: Checkerboard artifact score
            - radial_profile: Radial frequency profile
            - high_frequency_ratio: High-frequency energy ratio
    """
    try:
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1)
        
        h, w = magnitude.shape
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        radius = np.sqrt((x - cx)**2 + (y - cy)**2)
        
        # Compute all features
        entropy_score = _compute_frequency_entropy(magnitude)
        peak_score = _detect_spectral_peaks(magnitude)
        ring_score = _detect_ring_artifacts(magnitude, cx, cy)
        checkerboard_score = _detect_checkerboard_artifacts(magnitude)
        
        # Radial profile
        max_radius = min(cx, cy)
        radial_profile = []
        if max_radius > 10:
            bins = 10
            bin_edges = np.linspace(0, max_radius, bins + 1)
            for i in range(bins):
                mask = (radius >= bin_edges[i]) & (radius < bin_edges[i + 1])
                if np.sum(mask) > 0:
                    radial_profile.append(float(np.mean(magnitude[mask])))
        
        # High-frequency ratio
        hf_mask = radius > (max_radius * 0.6)
        if np.sum(hf_mask) > 0:
            lf_energy = np.mean(magnitude[~hf_mask]) if np.sum(~hf_mask) > 0 else 0
            hf_energy = np.mean(magnitude[hf_mask])
            hf_ratio = hf_energy / (lf_energy + 1e-8)
        else:
            hf_ratio = 0.0
        
        return {
            'score': frequency_domain_score(gray),
            'frequency_entropy': entropy_score,
            'spectral_peaks': peak_score,
            'ring_artifacts': ring_score,
            'checkerboard_artifacts': checkerboard_score,
            'radial_profile': radial_profile,
            'high_frequency_ratio': float(hf_ratio)
        }
    except Exception:
        return {
            'score': 0.5,
            'frequency_entropy': 0.0,
            'spectral_peaks': 0.0,
            'ring_artifacts': 0.0,
            'checkerboard_artifacts': 0.0,
            'radial_profile': [],
            'high_frequency_ratio': 0.0
        }

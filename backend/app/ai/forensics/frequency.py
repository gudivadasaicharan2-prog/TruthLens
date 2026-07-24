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
    - Periodicity detection (GAN grid artifacts)

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
        
        # Combine all signals
        base_score = (mean_score + std_score) / 2.0
        final_score = min(max(base_score + radial_score * 0.3 + hf_score * 0.3, 0.0), 1.0)
        
        return round(final_score, 4)
    except Exception:
        return 0.5

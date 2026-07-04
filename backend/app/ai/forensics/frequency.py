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

        return round((mean_score + std_score) / 2.0, 4)
    except Exception:
        return 0.5

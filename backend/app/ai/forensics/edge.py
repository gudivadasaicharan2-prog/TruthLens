"""
Edge Consistency Analysis Forensic Module
==========================================
Detects unnatural edge patterns characteristic of AI-generated images.
"""

import cv2
import numpy as np


def edge_consistency_score(gray: np.ndarray) -> float:
    """
    Edge consistency analysis — detects unnatural edge patterns.
    
    AI-generated images often exhibit:
    - Overly smooth edges (lack of natural sensor noise)
    - Perfectly straight lines (unnatural geometric precision)
    - Inconsistent edge sharpness across regions
    
    Real camera images have:
    - Natural edge variation due to lens aberrations
    - Slight edge noise from sensor characteristics
    - Varying edge sharpness based on focus depth
    
    Returns: float [0, 1] where 1 = suspicious (unnatural edges).
    """
    try:
        h, w = gray.shape
        
        # Edge detection using multiple methods
        edges_canny = cv2.Canny(gray, 50, 150)
        edges_sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        edges_sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edges_sobel = np.sqrt(edges_sobel_x**2 + edges_sobel_y**2)
        
        # Signal 1: Edge density analysis
        edge_density = float(np.sum(edges_canny > 0) / edges_canny.size)
        # Natural images typically have edge density between 0.02 and 0.15
        density_score = 0.0
        if edge_density < 0.01:  # Too few edges (over-smoothed)
            density_score = 0.4
        elif edge_density > 0.2:  # Too many edges (over-sharpened)
            density_score = 0.3
        
        # Signal 2: Edge sharpness consistency
        # Divide image into regions and check edge strength variation
        grid_size = 4
        h_step, w_step = h // grid_size, w // grid_size
        edge_strengths = []
        
        for i in range(grid_size):
            for j in range(grid_size):
                y_start, y_end = i * h_step, (i + 1) * h_step if i < grid_size - 1 else h
                x_start, x_end = j * w_step, (j + 1) * w_step if j < grid_size - 1 else w
                region_edges = edges_sobel[y_start:y_end, x_start:x_end]
                edge_strengths.append(float(np.mean(region_edges)))
        
        # Check consistency of edge strengths
        if len(edge_strengths) >= 4:
            edge_strength_cv = float(np.std(edge_strengths)) / (float(np.mean(edge_strengths)) + 1e-6)
            # Low CV suggests unnaturally uniform edge sharpness
            if edge_strength_cv < 0.2:
                consistency_score = 0.35
            elif edge_strength_cv < 0.35:
                consistency_score = 0.15
            else:
                consistency_score = 0.0
        else:
            consistency_score = 0.0
        
        # Signal 3: Straight line detection
        # AI images often have unnaturally straight lines
        lines = cv2.HoughLinesP(edges_canny, rho=1, theta=np.pi/180, threshold=50,
                                minLineLength=30, maxLineGap=10)
        
        if lines is not None:
            num_lines = len(lines)
            # Calculate line straightness (variance of angles)
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                angles.append(abs(angle) % 90)  # Normalize to 0-90 degrees
            
            if len(angles) > 5:
                angle_std = float(np.std(angles))
                # Low angle variance suggests many parallel/perfectly aligned lines
                if angle_std < 10:
                    line_score = 0.25
                elif angle_std < 20:
                    line_score = 0.1
                else:
                    line_score = 0.0
            else:
                line_score = 0.0
        else:
            line_score = 0.0
        
        # Signal 4: Edge noise analysis
        # Real images have natural noise along edges
        edge_pixels = gray[edges_canny > 0]
        if len(edge_pixels) > 100:
            edge_noise = float(np.std(edge_pixels))
            # Very low edge noise suggests AI smoothing
            if edge_noise < 5:
                noise_score = 0.3
            elif edge_noise < 10:
                noise_score = 0.1
            else:
                noise_score = 0.0
        else:
            noise_score = 0.0
        
        # Combine all signals
        final_score = min(max(
            density_score * 0.25 +
            consistency_score * 0.3 +
            line_score * 0.2 +
            noise_score * 0.25,
            0.0
        ), 1.0)
        
        return round(final_score, 4)
        
    except Exception:
        return 0.0

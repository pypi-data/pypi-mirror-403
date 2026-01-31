"""
Core utility functions for calculating Geometric Drift (Fisher Information Velocity).
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np


def calculate_fisher_velocity(
    current_psd: np.ndarray,
    previous_psd: np.ndarray,
    dt: float,
    frequencies: np.ndarray,
    delta_f: float,
    bands: Optional[Dict[str, Tuple[float, float]]] = None,
) -> Dict[str, float]:
    """
    Computes the Fisher Information Velocity (Geometric Drift) between two PSD snapshots.

    The metric is defined as the norm of the time-derivative of the PSD,
    weighted by the Fisher Information metric (1/S^2).

    Formula:
        v^2 = Integral [ (dS/dt / S)^2 ] df

    Args:
        current_psd: Array of PSD power values at time t.
        previous_psd: Array of PSD power values at time t - dt.
        dt: Time difference in seconds.
        frequencies: Array of frequency bins corresponding to the PSDs.
        delta_f: Frequency bin width (Hz).
        bands: Dictionary of frequency bands {'name': (f_min, f_max)} to compute.
               If None, computes 'total' over the entire provided spectrum.

    Returns:
        Dictionary mapping band names to drift velocity values.
    """
    if dt <= 0:
        raise ValueError("Time difference dt must be positive.")

    # 1. Compute Time Derivative: S_dot = (S_curr - S_prev) / dt
    diff = (current_psd - previous_psd) / dt

    # 2. Compute Integrand: (S_dot / S)^2
    # Handle division by zero or negative/zero power values safely
    valid = current_psd > 0
    integrand = np.zeros_like(current_psd)
    integrand[valid] = (diff[valid] / current_psd[valid]) ** 2

    # 3. Integrate over bands
    drift_results = {}
    bands_to_compute = bands.copy() if bands else {}

    if not bands_to_compute:
        # Default to total band if none provided
        # Extend upper bound to ensure coverage
        bands_to_compute = {"total": (frequencies[0], frequencies[-1] + delta_f * 0.5)}

    for name, (fmin, fmax) in bands_to_compute.items():
        # Mask frequencies within the band
        mask = (frequencies >= fmin) & (frequencies < fmax)

        if np.any(mask):
            # Integral [ ... ] df
            integral = np.sum(integrand[mask]) * delta_f
            drift_results[name] = np.sqrt(integral)
        else:
            drift_results[name] = 0.0

    return drift_results

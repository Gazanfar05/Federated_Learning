from __future__ import annotations

import numpy as np


def add_gaussian_noise(update, noise_multiplier: float = 0.5, delta: float = 1e-5):
    """Add Gaussian noise to a flat update in-place and return accompanied privacy metadata."""
    if noise_multiplier <= 0:
        return update, {"epsilon": None, "delta": delta, "noise_multiplier": noise_multiplier, "noise_added": False}

    if isinstance(update, dict):
        noisy = {}
        for key, value in update.items():
            arr = np.asarray(value, dtype=float)
            noise = np.random.normal(0.0, noise_multiplier, arr.shape)
            noisy[key] = arr + noise
        return noisy, {"epsilon": None, "delta": delta, "noise_multiplier": noise_multiplier, "noise_added": True}

    arr = np.asarray(update, dtype=float)
    noise = np.random.normal(0.0, noise_multiplier, arr.shape)
    return arr + noise, {"epsilon": None, "delta": delta, "noise_multiplier": noise_multiplier, "noise_added": True}


__all__ = ["add_gaussian_noise"]

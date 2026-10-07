from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .utils import derive_seed


@dataclass
class PrivacyMetadata:
    enabled: bool
    clip_norm: float
    epsilon: float
    delta: float
    noise_multiplier: float
    original_norm: float
    clipped_norm: float
    noise_std: float


def clip_update(update: np.ndarray, clip_norm: float) -> tuple[np.ndarray, dict[str, float]]:
    update = np.asarray(update, dtype=np.float32).ravel()
    original_norm = float(np.linalg.norm(update))
    if original_norm <= clip_norm or original_norm == 0.0:
        return update.copy(), {"original_norm": original_norm, "clipped_norm": original_norm, "clip_norm": clip_norm}
    scale = clip_norm / original_norm
    clipped = update * scale
    return clipped, {"original_norm": original_norm, "clipped_norm": float(np.linalg.norm(clipped)), "clip_norm": clip_norm}


def gaussian_noise_std(clip_norm: float, epsilon: float, delta: float) -> float:
    if epsilon <= 0 or delta <= 0 or delta >= 1:
        return 0.0
    return float((clip_norm * math.sqrt(2.0 * math.log(1.25 / delta))) / epsilon)


def apply_differential_privacy(update: np.ndarray, *, enabled: bool, clip_norm: float, epsilon: float, delta: float, seed_parts: tuple[object, ...]) -> tuple[np.ndarray, PrivacyMetadata]:
    clipped, clip_meta = clip_update(update, clip_norm)
    if not enabled:
        return clipped, PrivacyMetadata(False, clip_norm, epsilon, delta, 0.0, clip_meta["original_norm"], clip_meta["clipped_norm"], 0.0)
    noise_std = gaussian_noise_std(clip_norm, epsilon, delta)
    rng = np.random.default_rng(derive_seed(*seed_parts))
    noise = rng.normal(loc=0.0, scale=noise_std, size=clipped.shape).astype(np.float32)
    noisy = clipped + noise
    return noisy, PrivacyMetadata(True, clip_norm, epsilon, delta, noise_std / clip_norm if clip_norm else 0.0, clip_meta["original_norm"], clip_meta["clipped_norm"], noise_std)

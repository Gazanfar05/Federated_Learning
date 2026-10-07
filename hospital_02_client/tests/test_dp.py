from __future__ import annotations

import numpy as np

from app.differential_privacy import apply_differential_privacy, clip_update


def test_update_clipping():
    update = np.array([10.0, 0.0, 0.0], dtype=np.float32)
    clipped, meta = clip_update(update, 1.0)
    assert np.linalg.norm(clipped) <= 1.0001
    assert meta["original_norm"] > meta["clipped_norm"]


def test_dp_noise():
    update = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    noisy, meta = apply_differential_privacy(update, enabled=True, clip_norm=1.0, epsilon=2.0, delta=1e-5, seed_parts=("test", 1))
    assert noisy.shape == update.shape
    assert meta.enabled is True


def test_dp_disabled_mode():
    update = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    noisy, meta = apply_differential_privacy(update, enabled=False, clip_norm=1.0, epsilon=2.0, delta=1e-5, seed_parts=("test", 2))
    assert np.allclose(noisy, clip_update(update, 1.0)[0])
    assert meta.enabled is False

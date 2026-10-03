from __future__ import annotations

import numpy as np

from client.privacy.differential_privacy import add_gaussian_noise


def test_dp_noise_added_when_enabled():
    original = np.array([1.0, 2.0, 3.0])
    noisy, meta = add_gaussian_noise(original, noise_multiplier=0.5, delta=1e-5)
    assert np.allclose(noisy, original) is False
    assert meta['noise_added'] is True


def test_dp_noise_disabled_for_testing():
    original = np.array([1.0, 2.0, 3.0])
    noisy, meta = add_gaussian_noise(original, noise_multiplier=0.0, delta=1e-5)
    assert np.allclose(noisy, original)
    assert meta['noise_added'] is False

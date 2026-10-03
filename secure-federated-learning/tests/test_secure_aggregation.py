from __future__ import annotations

import numpy as np

from server.federated.secure_aggregation import SecureAggregator


def test_masking_roundtrip():
    aggregator = SecureAggregator(seed=7)
    values = np.array([1.2, -2.3, 3.4], dtype=np.float32)
    masked, mask = aggregator.mask_vector(values)
    unmasked = aggregator.unmask_vector(masked, mask)
    assert np.allclose(unmasked, values)

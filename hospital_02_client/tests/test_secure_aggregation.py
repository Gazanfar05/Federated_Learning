from __future__ import annotations

import numpy as np

from app.secure_aggregation import mask_update, unmask_update


def test_secure_aggregation_roundtrip():
    update = np.array([0.1, -0.2, 0.3], dtype=np.float32)
    masked, meta = mask_update(update, "hospital_02", 1, 1)
    restored = unmask_update(masked, meta)
    assert np.allclose(restored, update)

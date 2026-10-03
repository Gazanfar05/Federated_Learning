from __future__ import annotations

import numpy as np

from server.federated.anomaly_detection import flag_update


def test_extreme_update_is_flagged():
    reference = np.ones(8, dtype=np.float32)
    suspicious = np.full(8, 100.0, dtype=np.float32)
    result = flag_update(suspicious, reference, threshold=0.80)
    assert result["decision"] == "SUSPICIOUS"
    assert float(result["anomaly_score"]) > 0.80

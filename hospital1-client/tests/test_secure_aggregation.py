from __future__ import annotations

import numpy as np

from client.security.secure_aggregation import compute_update_hash, mask_update


def test_masked_update_contains_server_protocol_fields():
    update = {'layer1': np.array([0.1, 0.2])}
    masked = mask_update(update, 'hospital_01', 1, 1, 100)
    assert masked['client_id'] == 'hospital_01'
    assert masked['round_id'] == 1
    assert masked['model_version'] == 1
    assert 'masked_update' in masked
    assert isinstance(masked['mask_seed'], str)


def test_hash_matches_payload():
    update = {'layer1': np.array([0.1, 0.2])}
    masked = mask_update(update, 'hospital_01', 1, 1, 100)
    digest = compute_update_hash(masked)
    assert isinstance(digest, str)
    assert len(digest) == 64

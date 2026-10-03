from __future__ import annotations

from client.communication.serialization import deserialize_update, serialize_update


def test_serialize_deserialize_roundtrip():
    payload = {
        'client_id': 'hospital_01',
        'round_id': 2,
        'model_version': 2,
        'num_samples': 250,
        'protected_update': {'weights': [0.1, 0.2, 0.3]},
        'update_hash': 'abc123',
        'privacy_metadata': {'epsilon': None, 'delta': 1e-5}
    }
    text = serialize_update(payload)
    restored = deserialize_update(text)
    assert restored == payload

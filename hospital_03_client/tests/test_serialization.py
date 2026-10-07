from __future__ import annotations

from app.serialization import compute_update_hash, deserialize_payload, serialize_payload


def test_serialization_determinism():
    payload = {
        "client_id": "hospital_03",
        "round_id": 1,
        "model_version": 1,
        "num_samples": 10,
        "protected_update": [0.1, 0.2, 0.3],
        "timestamp": "2026-10-07T00:00:00Z",
    }
    first = serialize_payload(payload)
    second = serialize_payload(payload)
    assert first == second
    assert deserialize_payload(first) == payload


def test_update_hash():
    payload = {
        "client_id": "hospital_03",
        "round_id": 1,
        "model_version": 1,
        "num_samples": 10,
        "protected_update": [0.1, 0.2, 0.3],
        "timestamp": "2026-10-07T00:00:00Z",
    }
    assert compute_update_hash(payload) == compute_update_hash(payload)

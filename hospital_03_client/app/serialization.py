from __future__ import annotations

from typing import Any

import numpy as np

from .utils import sha256_hex, stable_json_bytes


def _json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.astype(np.float32).ravel().tolist()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value


def canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return stable_json_bytes(_json_ready(payload))


def compute_update_hash(payload: dict[str, Any]) -> str:
    return sha256_hex(canonical_payload_bytes(payload))


def serialize_payload(payload: dict[str, Any]) -> str:
    return canonical_payload_bytes(payload).decode("utf-8")


def deserialize_payload(serialized: str) -> dict[str, Any]:
    import json

    return json.loads(serialized)

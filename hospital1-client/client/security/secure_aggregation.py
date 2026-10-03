from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np


def mask_update(update: Any, client_id: str, round_id: int | str, model_version: int | str, num_samples: int):
    """Create a client-side masking placeholder that preserves the server-visible schema. This does not claim production-grade secure aggregation."""
    payload = {
        "client_id": client_id,
        "round_id": round_id,
        "model_version": model_version,
        "num_samples": num_samples,
        "masked_update": _serialize_for_transport(update),
        "masking_scheme": "client_side_masking",
        "mask_seed": hashlib.sha256(f"{client_id}:{round_id}:{model_version}".encode()).hexdigest()[:16],
    }
    return payload


def _serialize_for_transport(data):
    if isinstance(data, dict):
        return {k: _serialize_for_transport(v) for k, v in data.items()}
    if isinstance(data, np.ndarray):
        return data.tolist()
    if isinstance(data, (list, tuple)):
        return [_serialize_for_transport(v) for v in data]
    if isinstance(data, (float, int, str, bool)) or data is None:
        return data
    return str(data)


def compute_update_hash(serialized_payload: dict) -> str:
    canonical = json.dumps(serialized_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


__all__ = ["mask_update", "compute_update_hash"]

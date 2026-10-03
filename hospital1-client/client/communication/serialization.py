from __future__ import annotations

import json
from typing import Any


def serialize_update(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def deserialize_update(serialized: str) -> dict:
    return json.loads(serialized)


def safe_payload(payload: dict) -> dict:
    sanitized = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            sanitized[key] = safe_payload(value)
        elif isinstance(value, list):
            sanitized[key] = [safe_payload(v) if isinstance(v, dict) else v for v in value]
        elif isinstance(value, (str, int, float, bool)) or value is None:
            sanitized[key] = value
        else:
            sanitized[key] = str(value)
    return sanitized


__all__ = ["serialize_update", "deserialize_update", "safe_payload"]

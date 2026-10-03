from __future__ import annotations

import hashlib
import json


def sha256_hex(data):
    if isinstance(data, (dict, list, tuple)):
        payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    else:
        payload = str(data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


__all__ = ["sha256_hex"]

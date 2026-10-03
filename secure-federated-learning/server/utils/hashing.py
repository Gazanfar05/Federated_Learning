from __future__ import annotations

import hashlib
from typing import Any


def stable_hash(payload: Any) -> str:
    serialized = repr(payload).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()

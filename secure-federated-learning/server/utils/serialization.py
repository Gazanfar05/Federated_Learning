from __future__ import annotations

import json
from typing import Any


def json_safe_dump(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))

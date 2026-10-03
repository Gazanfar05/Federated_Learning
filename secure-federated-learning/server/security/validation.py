from __future__ import annotations

from typing import Any


def validate_numeric_payload(value: Any, field_name: str) -> None:
    if value is None:
        raise ValueError(f"{field_name} cannot be null.")
    try:
        float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc


def ensure_positive(value: int | float, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive.")

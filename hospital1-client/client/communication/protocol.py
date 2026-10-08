from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_auth_payload(
    client_id: str,
    round_id: int | str | None = None,
    status: str | None = None,
    certificate_identity: str | None = None,
):
    payload = {
        "client_id": client_id,
        "certificate_identity": certificate_identity or client_id,
    }
    if round_id is not None:
        payload["round_id"] = round_id
    if status is not None:
        payload["status"] = status
    return payload


def build_update_payload(
    client_id: str,
    round_id: int | str,
    model_version: int | str,
    protected_update: Any,
    num_samples: int,
    privacy_metadata: dict,
    update_hash: str,
    raw_update: Any | None = None,
    reference_model: Any | None = None,
):
    def _as_list(value: Any) -> list[float] | Any:
        if isinstance(value, dict):
            flattened: list[float] = []
            for nested in value.values():
                if isinstance(nested, (list, tuple)):
                    flattened.extend(float(x) for x in nested)
                else:
                    flattened.append(float(nested))
            return flattened
        if isinstance(value, (list, tuple)):
            return [float(x) for x in value]
        if hasattr(value, "tolist"):
            return [float(x) for x in value.tolist()]
        return value

    payload = {
        "client_id": client_id,
        "round_id": round_id,
        "model_version": model_version,
        "num_samples": num_samples,
        "protected_update": _as_list(protected_update),
        "raw_update": _as_list(raw_update) if raw_update is not None else None,
        "reference_model": _as_list(reference_model) if reference_model is not None else None,
        "update_hash": update_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return payload


__all__ = ["build_auth_payload", "build_update_payload"]

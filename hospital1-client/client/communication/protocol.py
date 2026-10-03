from __future__ import annotations

from typing import Any


def build_auth_payload(client_id: str, round_id: int | str = 0, status: str = "connected"):
    return {
        "client_id": client_id,
        "round_id": round_id,
        "status": status,
        "timestamp": None,
    }


def build_update_payload(client_id: str, round_id: int | str, model_version: int | str, protected_update: Any, num_samples: int, privacy_metadata: dict, update_hash: str):
    return {
        "client_id": client_id,
        "round_id": round_id,
        "model_version": model_version,
        "num_samples": num_samples,
        "protected_update": protected_update,
        "update_hash": update_hash,
        "privacy_metadata": privacy_metadata,
    }


__all__ = ["build_auth_payload", "build_update_payload"]

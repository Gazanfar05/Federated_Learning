from __future__ import annotations

import os


def validate_server_response(response):
    if response is None:
        return False
    data = getattr(response, "json", None)
    if callable(data):
        try:
            return isinstance(data(), dict)
        except Exception:
            return False
    return True


def ensure_no_patient_data(payload):
    if not isinstance(payload, dict):
        return True
    forbidden = {
        "patient_id",
        "name",
        "age",
        "glucose",
        "blood_pressure",
        "bmi",
        "insulin",
        "pregnancies",
        "outcome",
    }
    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key).lower() in forbidden:
                    return False
                if not walk(child):
                    return False
        elif isinstance(value, list):
            for child in value:
                if not walk(child):
                    return False
        return True
    return walk(payload)


__all__ = ["validate_server_response", "ensure_no_patient_data"]

from __future__ import annotations

import numpy as np


def _align_shapes(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    a = np.asarray(a, dtype=np.float32).ravel()
    b = np.asarray(b, dtype=np.float32).ravel()
    size = min(a.size, b.size)
    return a[:size], b[:size]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a, b = _align_shapes(a, b)
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def compute_anomaly_score(update: np.ndarray, reference: np.ndarray) -> float:
    update, reference = _align_shapes(update, reference)
    update_norm = float(np.linalg.norm(update))
    ref_norm = float(np.linalg.norm(reference))
    magnitude_ratio = update_norm / (ref_norm + 1e-9)
    similarity = cosine_similarity(update, reference)
    score = 0.6 * abs(magnitude_ratio - 1.0) + 0.4 * (1.0 - abs(similarity))
    return float(np.clip(score, 0.0, 1.0))


def flag_update(update: np.ndarray, reference: np.ndarray, threshold: float = 0.80) -> dict[str, float | str]:
    score = compute_anomaly_score(update, reference)
    if score > threshold:
        return {
            "anomaly_score": score,
            "threshold": threshold,
            "decision": "SUSPICIOUS",
            "reason": "Update magnitude or direction diverges from the reference model too strongly.",
        }
    return {
        "anomaly_score": score,
        "threshold": threshold,
        "decision": "NORMAL",
        "reason": "Within expected update range.",
    }

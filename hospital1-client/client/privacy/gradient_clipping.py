from __future__ import annotations

import numpy as np


def clip_update(update, clipping_norm: float):
    """Clip a flat update tensor or vector to have L2 norm <= clipping_norm."""
    if clipping_norm <= 0:
        raise ValueError("clipping_norm must be positive")
    if isinstance(update, dict):
        flat = np.concatenate([np.asarray(v, dtype=float).ravel() for v in update.values()])
    else:
        flat = np.asarray(update, dtype=float).ravel()

    norm = float(np.linalg.norm(flat))
    if norm > clipping_norm:
        clipped = flat * (clipping_norm / norm)
        if isinstance(update, dict):
            result = {}
            pointer = 0
            for key, value in update.items():
                size = np.asarray(value, dtype=float).size
                result[key] = clipped[pointer : pointer + size].reshape(np.asarray(value).shape)
                pointer += size
            return result, {"original_norm": norm, "clipped_norm": float(np.linalg.norm(clipped)), "clipping_applied": True}
        return clipped, {"original_norm": norm, "clipped_norm": float(np.linalg.norm(clipped)), "clipping_applied": True}

    if isinstance(update, dict):
        return update, {"original_norm": norm, "clipped_norm": norm, "clipping_applied": False}
    return update, {"original_norm": norm, "clipped_norm": norm, "clipping_applied": False}


__all__ = ["clip_update"]

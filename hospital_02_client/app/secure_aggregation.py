from __future__ import annotations

import numpy as np

from .utils import derive_seed


def mask_update(update: np.ndarray, client_id: str, round_id: int, model_version: int, mask_scale: float = 0.05) -> tuple[np.ndarray, dict[str, object]]:
    vector = np.asarray(update, dtype=np.float32).ravel()
    seed = derive_seed(client_id, round_id, model_version, vector.size)
    rng = np.random.default_rng(seed)
    mask = rng.normal(loc=0.0, scale=mask_scale, size=vector.size).astype(np.float32)
    masked = vector + mask
    return masked, {"mask_seed": seed, "mask_scale": mask_scale, "vector_size": int(vector.size)}


def unmask_update(masked_update: np.ndarray, mask_metadata: dict[str, object]) -> np.ndarray:
    seed = int(mask_metadata["mask_seed"])
    mask_scale = float(mask_metadata["mask_scale"])
    vector = np.asarray(masked_update, dtype=np.float32).ravel()
    rng = np.random.default_rng(seed)
    mask = rng.normal(loc=0.0, scale=mask_scale, size=vector.size).astype(np.float32)
    return vector - mask

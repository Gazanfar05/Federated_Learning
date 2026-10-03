from __future__ import annotations

import numpy as np


class SecureAggregator:
    """Academic masked aggregation implementation.

    This is not claimed to be a production-grade cryptographic secure aggregation
    protocol. It demonstrates the design pattern: client-side masking, server-side
    aggregated masked values, and mask cancellation for a classroom project.
    """

    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)

    def mask_vector(self, vector: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        mask = self.rng.standard_normal(vector.shape, dtype=np.float32)
        return vector + mask, mask

    def unmask_vector(self, masked_vector: np.ndarray, mask: np.ndarray) -> np.ndarray:
        return masked_vector - mask

    def aggregate_masked_updates(self, masked_updates: list[np.ndarray]) -> np.ndarray:
        if not masked_updates:
            raise ValueError("No masked updates to aggregate.")
        total = np.zeros_like(masked_updates[0], dtype=np.float32)
        for item in masked_updates:
            total = total + item
        return total

    def aggregate_and_unmask(self, updates: list[np.ndarray], masks: list[np.ndarray]) -> np.ndarray:
        if len(updates) != len(masks):
            raise ValueError("Each update must have one matching mask.")
        masked = [u + m for u, m in zip(updates, masks)]
        aggregated_masked = self.aggregate_masked_updates(masked)
        aggregated_mask = np.sum(masks, axis=0)
        return aggregated_masked - aggregated_mask

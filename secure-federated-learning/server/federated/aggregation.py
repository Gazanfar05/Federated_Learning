from __future__ import annotations

from typing import Iterable

import torch


def aggregate_state_dicts(state_dicts: Iterable[dict[str, torch.Tensor]], sample_counts: Iterable[int]) -> dict[str, torch.Tensor]:
    models = list(state_dicts)
    weights = list(sample_counts)
    if not models:
        raise ValueError("No client models were supplied.")
    total = sum(weights)
    if total <= 0:
        raise ValueError("Total sample count must be positive.")

    aggregated: dict[str, torch.Tensor] = {}
    for key in models[0].keys():
        weighted = torch.zeros_like(models[0][key])
        for model, weight in zip(models, weights):
            weighted += weight * model[key]
        aggregated[key] = weighted / total
    return aggregated

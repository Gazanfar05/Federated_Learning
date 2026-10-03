from __future__ import annotations

from copy import deepcopy

import torch


def weighted_fedavg(global_model: torch.nn.Module, client_models: list[torch.nn.Module], sample_counts: list[int]) -> torch.nn.Module:
    """Compute the weighted FedAvg of a set of client models.

    The model weight is proportional to the number of local samples used to train that client.
    """
    if not client_models:
        return deepcopy(global_model)

    total_samples = sum(sample_counts)
    if total_samples <= 0:
        raise ValueError("Total samples must be positive.")

    aggregated = {}
    for key in global_model.state_dict().keys():
        weighted_sum = torch.zeros_like(global_model.state_dict()[key])
        for model, count in zip(client_models, sample_counts):
            weighted_sum += count * model.state_dict()[key]
        aggregated[key] = weighted_sum / total_samples

    updated = deepcopy(global_model)
    updated.load_state_dict(aggregated)
    return updated

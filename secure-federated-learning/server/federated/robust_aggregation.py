from __future__ import annotations

from typing import Sequence

import torch

from server.federated.fedavg import weighted_fedavg


def robust_aggregate(
    global_model: torch.nn.Module,
    client_models: Sequence[torch.nn.Module],
    sample_counts: Sequence[int],
    anomaly_scores: Sequence[float],
    threshold: float = 0.8,
) -> tuple[torch.nn.Module, list[int]]:
    """Filter suspicious client models, then apply sample-weighted FedAvg.

    Returns the unchanged global model if no clients pass the filter.
    The returned indices refer to the original client_models sequence.
    """
    if not (
        len(client_models) == len(sample_counts) == len(anomaly_scores)
    ):
        raise ValueError(
            "client_models, sample_counts, and anomaly_scores must have equal lengths."
        )

    if any(count <= 0 for count in sample_counts):
        raise ValueError("Every client sample count must be positive.")

    valid_indices = [
        index
        for index, score in enumerate(anomaly_scores)
        if score <= threshold
    ]

    if not valid_indices:
        # FedAvg with an empty client list returns a copy of the global model.
        return weighted_fedavg(global_model, [], []), []

    accepted_models = [client_models[index] for index in valid_indices]
    accepted_weights = [sample_counts[index] for index in valid_indices]

    return (
        weighted_fedavg(global_model, accepted_models, accepted_weights),
        valid_indices,
    )

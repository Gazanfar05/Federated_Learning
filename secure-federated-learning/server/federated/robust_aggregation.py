from __future__ import annotations

from typing import Sequence

import torch

from server.federated.fedavg import weighted_fedavg


def robust_aggregate(global_model: torch.nn.Module, client_models: Sequence[torch.nn.Module], sample_counts: Sequence[int], anomaly_scores: Sequence[float], threshold: float = 0.8) -> tuple[torch.nn.Module, list[int]]:
    """Reject or down-weight suspicious clients before FedAvg.

    This keeps the implementation explainable while defending against simulated
    poisoning attempts.
    """
    valid_indices = [index for index, score in enumerate(anomaly_scores) if score <= threshold]
    if not valid_indices:
        return weighted_fedavg(global_model, list(client_models), list(sample_counts)), []

    accepted_models = [client_models[idx] for idx in valid_indices]
    accepted_weights = [sample_counts[idx] for idx in valid_indices]
    return weighted_fedavg(global_model, accepted_models, accepted_weights), valid_indices

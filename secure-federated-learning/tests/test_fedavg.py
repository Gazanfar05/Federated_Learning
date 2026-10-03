from __future__ import annotations

import torch

from server.federated.fedavg import weighted_fedavg
from server.models.diabetes_model import DiabetesMLP


def test_weighted_fedavg():
    model_a = DiabetesMLP()
    model_b = DiabetesMLP()

    for parameter in model_a.parameters():
        parameter.data.fill_(1.0)
    for parameter in model_b.parameters():
        parameter.data.fill_(3.0)

    result = weighted_fedavg(model_a, [model_a, model_b], [2, 1])

    first_weight = result.state_dict()["net.0.weight"]
    expected = torch.full_like(first_weight, 5.0 / 3.0)
    assert torch.allclose(first_weight, expected)

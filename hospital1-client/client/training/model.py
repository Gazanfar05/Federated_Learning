from __future__ import annotations

import torch
from torch import nn


class DiabetesMLP(nn.Module):
    """Binary classifier for diabetes prediction."""

    def __init__(self, input_dim: int = 8):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Dropout(p=0.1),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 1),
        )

    def forward(self, x):
        return self.network(x)

    def get_flattened_parameters(self):
        return torch.cat([p.detach().flatten() for p in self.parameters()])


def create_model(input_dim: int = 8) -> DiabetesMLP:
    return DiabetesMLP(input_dim=input_dim)


__all__ = ["DiabetesMLP", "create_model"]

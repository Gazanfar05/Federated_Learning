from __future__ import annotations

import torch
from torch import nn


class DiabetesMLP(nn.Module):
    """Small MLP for tabular diabetes prediction.

    This is intentionally small to keep model sizing manageable across local client
    training and server aggregation on a LAN in a classroom deployment.
    """

    def __init__(self, input_dim: int = 8, hidden_dim: int = 16) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)

    @staticmethod
    def default_global_model() -> "DiabetesMLP":
        return DiabetesMLP()

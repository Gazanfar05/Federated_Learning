from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

from .utils import flatten_state_dict


class DiabetesMLP(nn.Module):
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


def build_model(input_dim: int = 8) -> DiabetesMLP:
    return DiabetesMLP(input_dim=input_dim)


def state_dict_to_vector(model: nn.Module) -> np.ndarray:
    return flatten_state_dict(model.state_dict())


def vector_to_state_dict(model: nn.Module, vector: np.ndarray) -> dict[str, torch.Tensor]:
    vector = np.asarray(vector, dtype=np.float32).ravel()
    state = model.state_dict()
    offset = 0
    restored: dict[str, torch.Tensor] = {}
    for key in sorted(state):
        tensor = state[key]
        count = int(np.prod(tensor.shape))
        slice_ = vector[offset : offset + count]
        if slice_.size != count:
            raise ValueError(f"Insufficient values for tensor {key!r}.")
        restored[key] = torch.tensor(slice_.reshape(tensor.shape), dtype=tensor.dtype)
        offset += count
    return restored


def model_update_vector(global_model: nn.Module, local_model: nn.Module) -> np.ndarray:
    return state_dict_to_vector(local_model) - state_dict_to_vector(global_model)


@dataclass
class TrainingResult:
    model: nn.Module
    loss: float
    accuracy: float
    num_samples: int


def _evaluate(model: nn.Module, loader: torch.utils.data.DataLoader) -> tuple[float, float]:
    criterion = nn.BCEWithLogitsLoss()
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    with torch.no_grad():
        for features, labels in loader:
            logits = model(features)
            loss = criterion(logits, labels)
            total_loss += float(loss.item()) * len(features)
            predictions = (torch.sigmoid(logits) >= 0.5).float()
            correct += int((predictions == labels).sum().item())
            total += len(features)
    average_loss = total_loss / max(total, 1)
    accuracy = correct / max(total, 1)
    return average_loss, accuracy


def train_local_model(model: nn.Module, train_loader: torch.utils.data.DataLoader, val_loader: torch.utils.data.DataLoader, epochs: int, learning_rate: float) -> TrainingResult:
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.BCEWithLogitsLoss()
    model.train()
    for _ in range(epochs):
        for features, labels in train_loader:
            optimizer.zero_grad(set_to_none=True)
            logits = model(features)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
    val_loss, val_accuracy = _evaluate(model, val_loader)
    return TrainingResult(model=model, loss=val_loss, accuracy=val_accuracy, num_samples=len(train_loader.dataset))

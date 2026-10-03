from __future__ import annotations

import copy

import torch
from torch import nn

from client.training.evaluation import evaluate_model
from client.training.model import DiabetesMLP
from client.utils.metrics import compute_classification_metrics, update_norm


def train_local_model(global_model, local_dataset, epochs: int = 3, learning_rate: float = 0.001, batch_size: int = 32):
    model = copy.deepcopy(global_model)
    model.train()
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # dataset is expected to be a TensorDataset with 2-tensor pairs.
    loader = torch.utils.data.DataLoader(local_dataset, batch_size=batch_size, shuffle=True)

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for xb, yb in loader:
            optimizer.zero_grad()
            logits = model(xb).squeeze(-1)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * xb.size(0)
        epoch_loss = running_loss / len(loader.dataset)

    validation_metrics = evaluate_model(model, loader)
    training_metrics = {
        "training_loss": float(epoch_loss),
        "validation_loss": float(validation_metrics["loss"]),
        "accuracy": float(validation_metrics["accuracy"]),
        "f1": float(validation_metrics["f1"]),
    }

    local_update = {
        "model_state": model.state_dict(),
        "training_metrics": training_metrics,
        "num_samples": len(local_dataset),
    }
    return model, local_update


def model_delta(global_model, local_model):
    delta = {}
    for name, param in global_model.state_dict().items():
        delta[name] = local_model.state_dict()[name] - param
    return delta


__all__ = ["train_local_model", "model_delta"]

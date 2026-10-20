"""PyTorch task runner for binary diabetes prediction."""

import numpy as np
import torch
from torch import nn

from openfl.federated import PyTorchTaskRunner
from openfl.utilities import Metric


class DiabetesTaskRunner(PyTorchTaskRunner):
    """Compact MLP matching the dashboard's diabetes model topology."""

    def __init__(self, device="cpu", learning_rate=0.001, **kwargs):
        super().__init__(device=device, **kwargs)
        self.model = nn.Sequential(
            nn.Linear(8, 16), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(16, 16), nn.ReLU(), nn.Linear(16, 1),
        )
        self.to(self.device)
        self.optimizer = torch.optim.Adam(self.parameters(), lr=learning_rate)
        self.loss_fn = nn.BCEWithLogitsLoss()

    def forward(self, features):
        return self.model(features).squeeze(-1)

    def train_(self, train_dataloader):
        losses = []
        for features, targets in train_dataloader:
            features = torch.as_tensor(features, dtype=torch.float32, device=self.device)
            targets = torch.as_tensor(targets, dtype=torch.float32, device=self.device)
            self.optimizer.zero_grad()
            loss = self.loss_fn(self(features), targets)
            loss.backward()
            self.optimizer.step()
            losses.append(loss.detach().cpu().item())
        return Metric(name="loss", value=np.array(np.mean(losses), dtype=np.float32))

    def validate_(self, validation_dataloader):
        correct = total = 0
        with torch.no_grad():
            for features, targets in validation_dataloader:
                features = torch.as_tensor(features, dtype=torch.float32, device=self.device)
                targets = torch.as_tensor(targets, dtype=torch.float32, device=self.device)
                predictions = (torch.sigmoid(self(features)) >= 0.5).to(targets.dtype)
                correct += int((predictions == targets).sum().item())
                total += int(targets.numel())
        return Metric(name="accuracy", value=np.array(correct / total, dtype=np.float32))

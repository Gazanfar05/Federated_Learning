from __future__ import annotations

import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def evaluate_model(model, dataloader):
    model.eval()
    y_true = []
    y_pred = []
    losses = []
    criterion = torch.nn.BCEWithLogitsLoss()

    with torch.no_grad():
        for xb, yb in dataloader:
            logits = model(xb)
            probs = torch.sigmoid(logits).squeeze(-1)
            predictions = (probs >= 0.5).float()
            loss = criterion(logits.squeeze(-1), yb)
            losses.append(loss.item())
            y_true.extend(yb.cpu().numpy().astype(int).tolist())
            y_pred.extend(predictions.cpu().numpy().astype(int).tolist())

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    metrics = {
        "loss": float(np.mean(losses)) if losses else 0.0,
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    return metrics


__all__ = ["evaluate_model"]

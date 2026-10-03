from __future__ import annotations

import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def compute_classification_metrics(y_true, y_pred, y_prob=None):
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }
    if y_prob is not None:
        try:
            from sklearn.metrics import roc_auc_score

            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except Exception:
            pass
    return metrics


def update_norm(parameters):
    if hasattr(parameters, "detach"):
        flat = parameters.detach().cpu().numpy().ravel()
    else:
        flat = np.asarray(parameters, dtype=float).ravel()
    return float(np.linalg.norm(flat))


__all__ = ["compute_classification_metrics", "update_norm"]

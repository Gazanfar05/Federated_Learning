"""Local-only data loading for the diabetes OpenFL experiment."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from openfl.federated import PyTorchDataLoader


class DiabetesDataLoader(PyTorchDataLoader):
    """Load one collaborator's tabular diabetes data and make a local split."""

    def __init__(self, data_path=None, batch_size=32, validation_fraction=0.2, random_seed=42, **kwargs):
        super().__init__(batch_size=batch_size, random_seed=random_seed, **kwargs)
        self.feature_shape = [8]
        self.num_classes = 2
        if data_path is None:
            return
        features, labels = _read_diabetes_csv(Path(data_path))
        if not 0 < validation_fraction < 1:
            raise ValueError("validation_fraction must be between 0 and 1.")
        if len(features) < 10:
            raise ValueError("Each collaborator needs at least 10 local rows.")
        order = np.random.default_rng(random_seed).permutation(len(features))
        split_at = max(1, min(len(features) - 1, int(len(features) * (1 - validation_fraction))))
        train_idx, valid_idx = order[:split_at], order[split_at:]
        train_features = features[train_idx]
        # Standardization is fitted locally; population statistics are not shared.
        mean, scale = train_features.mean(axis=0), train_features.std(axis=0)
        scale[scale == 0] = 1.0
        self.X_train = ((train_features - mean) / scale).astype(np.float32)
        self.y_train = labels[train_idx].astype(np.float32)
        self.X_valid = ((features[valid_idx] - mean) / scale).astype(np.float32)
        self.y_valid = labels[valid_idx].astype(np.float32)

    def get_feature_shape(self):
        return self.feature_shape

    def get_num_classes(self):
        return self.num_classes


def _read_diabetes_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f"Collaborator data file does not exist: {path}")
    with path.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.reader(csv_file))
    if len(rows) < 2:
        raise ValueError(f"{path} must contain a header and at least one data row.")
    header = [cell.strip() for cell in rows[0]]
    try:
        target_index = next(i for i, name in enumerate(header) if name.lower() == "outcome")
    except StopIteration:
        target_index = len(header) - 1
    if len(header) != 9:
        raise ValueError("Expected exactly 8 feature columns and 1 target column.")
    values, targets = [], []
    for line_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(header):
            raise ValueError(f"Row {line_number} has {len(row)} cells; expected {len(header)}.")
        try:
            numeric = [float(cell) for cell in row]
        except ValueError as exc:
            raise ValueError(f"Row {line_number} contains a non-numeric value.") from exc
        target = numeric.pop(target_index)
        if target not in (0.0, 1.0):
            raise ValueError(f"Row {line_number} target must be 0 or 1.")
        values.append(numeric)
        targets.append(target)
    return np.asarray(values, dtype=np.float32), np.asarray(targets, dtype=np.float32)

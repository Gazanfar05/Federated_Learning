from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

from client.config import DATA_PATH, DATA_SPLIT_SEED


EXPECTED_COLUMNS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
    "Outcome",
]


def load_hospital1_csv(path: str | None = None) -> pd.DataFrame:
    csv_path = path or DATA_PATH
    df = pd.read_csv(csv_path)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")
    return df


def prepare_local_dataset(path: str | None = None, test_size: float = 0.2, val_size: float = 0.2):
    df = load_hospital1_csv(path)
    data = df.copy()

    # Deterministic handling of missing values.
    for col in ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]:
        median = data[col].median()
        data[col] = data[col].fillna(median)

    X = data.drop(columns=["Outcome"]).astype(float)
    y = data["Outcome"].astype(int)

    # Deterministic split: train/validation/test with fixed seed.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=DATA_SPLIT_SEED, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=val_size / (1.0 - test_size), random_state=DATA_SPLIT_SEED, stratify=y_train
    )

    # Standardize features deterministically.
    means = X_train.mean(axis=0)
    stds = X_train.std(axis=0).replace(0, 1.0)
    X_train = (X_train - means) / stds
    X_val = (X_val - means) / stds
    X_test = (X_test - means) / stds

    train_ds = TensorDataset(torch.tensor(X_train.to_numpy(), dtype=torch.float32), torch.tensor(y_train.to_numpy(), dtype=torch.float32))
    val_ds = TensorDataset(torch.tensor(X_val.to_numpy(), dtype=torch.float32), torch.tensor(y_val.to_numpy(), dtype=torch.float32))
    test_ds = TensorDataset(torch.tensor(X_test.to_numpy(), dtype=torch.float32), torch.tensor(y_test.to_numpy(), dtype=torch.float32))

    return {
        "train": train_ds,
        "val": val_ds,
        "test": test_ds,
        "feature_means": means.to_dict(),
        "feature_stds": stds.to_dict(),
        "sample_counts": {
            "train": len(train_ds),
            "val": len(val_ds),
            "test": len(test_ds),
        },
    }


def get_data_loader(dataset, batch_size: int = 32, shuffle: bool = True):
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


__all__ = ["EXPECTED_COLUMNS", "load_hospital1_csv", "prepare_local_dataset", "get_data_loader"]

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset


FEATURE_COLUMNS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]
LABEL_COLUMN = "Outcome"


@dataclass
class PreprocessedData:
    feature_names: list[str]
    input_dim: int
    train_loader: DataLoader
    val_loader: DataLoader
    x_train: np.ndarray
    y_train: np.ndarray
    x_val: np.ndarray
    y_val: np.ndarray
    imputer: SimpleImputer
    scaler: StandardScaler


def load_dataset(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = [column for column in FEATURE_COLUMNS + [LABEL_COLUMN] if column not in frame.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")
    return frame


def prepare_data(path: str | Path, batch_size: int, validation_ratio: float = 0.2, seed: int = 42) -> PreprocessedData:
    frame = load_dataset(path)
    features = frame[FEATURE_COLUMNS].copy()
    labels = frame[LABEL_COLUMN].astype(np.float32).to_numpy()

    x_train, x_val, y_train, y_val = train_test_split(
        features.to_numpy(dtype=np.float32),
        labels,
        test_size=validation_ratio,
        random_state=seed,
        stratify=labels if len(np.unique(labels)) > 1 else None,
    )

    imputer = SimpleImputer(strategy="median")
    scaler = StandardScaler()

    x_train = imputer.fit_transform(x_train)
    x_val = imputer.transform(x_val)
    x_train = scaler.fit_transform(x_train)
    x_val = scaler.transform(x_val)

    train_dataset = TensorDataset(
        torch.tensor(x_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32),
    )
    val_dataset = TensorDataset(
        torch.tensor(x_val, dtype=torch.float32),
        torch.tensor(y_val, dtype=torch.float32),
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    return PreprocessedData(
        feature_names=FEATURE_COLUMNS,
        input_dim=len(FEATURE_COLUMNS),
        train_loader=train_loader,
        val_loader=val_loader,
        x_train=x_train,
        y_train=y_train,
        x_val=x_val,
        y_val=y_val,
        imputer=imputer,
        scaler=scaler,
    )

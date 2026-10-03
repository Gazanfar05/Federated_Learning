from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from client.config import DATA_PATH, ROOT_DIR


def summarize_dataset(path: str | None = None):
    csv_path = path or DATA_PATH
    df = pd.read_csv(csv_path)
    summary = {
        "samples": int(len(df)),
        "class_distribution": df["Outcome"].value_counts().sort_index().to_dict(),
        "feature_statistics": df.describe().to_dict(),
        "columns": list(df.columns),
    }
    return summary


def save_preprocessing_summary(path: str | None = None):
    summary = summarize_dataset(path)
    output_path = Path(path or str(ROOT_DIR / "models" / "preprocessing_summary.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    return summary


__all__ = ["summarize_dataset", "save_preprocessing_summary"]

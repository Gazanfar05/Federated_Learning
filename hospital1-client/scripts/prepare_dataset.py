from __future__ import annotations

import pandas as pd

from client.training.dataset import prepare_local_dataset
from client.training.preprocessing import summarize_dataset


if __name__ == "__main__":
    summary = summarize_dataset()
    print("Hospital 1 samples:", summary["samples"])
    print("Class distribution:", summary["class_distribution"])
    print("Feature statistics:", summary["feature_statistics"]) 
    dataset = prepare_local_dataset()
    print("Train/validation/test split:", dataset["sample_counts"])

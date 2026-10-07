from __future__ import annotations

import numpy as np

from app.preprocessing import FEATURE_COLUMNS, LABEL_COLUMN, load_dataset, prepare_data


def test_dataset_loading():
    frame = load_dataset("data/hospital3.csv")
    assert list(frame.columns) == FEATURE_COLUMNS + [LABEL_COLUMN]
    assert len(frame) > 0


def test_missing_values_and_split():
    data = prepare_data("data/hospital3.csv", batch_size=4)
    assert data.input_dim == 8
    assert data.x_train.shape[1] == 8
    assert data.x_val.shape[1] == 8
    assert np.isfinite(data.x_train).all()
    assert np.isfinite(data.x_val).all()
    assert len(data.train_loader.dataset) > 0

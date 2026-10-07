from __future__ import annotations

import torch

from app.preprocessing import prepare_data
from app.training import build_model, model_update_vector, train_local_model


def test_model_creation():
    model = build_model()
    assert sum(p.numel() for p in model.parameters()) == 433


def test_local_training():
    data = prepare_data("data/hospital2.csv", batch_size=4)
    model = build_model(input_dim=data.input_dim)
    result = train_local_model(model, data.train_loader, data.val_loader, epochs=1, learning_rate=0.01)
    assert isinstance(result.model, torch.nn.Module)
    assert result.num_samples > 0


def test_update_generation():
    data = prepare_data("data/hospital2.csv", batch_size=4)
    global_model = build_model(input_dim=data.input_dim)
    local_model = build_model(input_dim=data.input_dim)
    vector = model_update_vector(global_model, local_model)
    assert vector.shape[0] == 433

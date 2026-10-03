from __future__ import annotations

import torch

from client.training.dataset import prepare_local_dataset
from client.training.local_trainer import train_local_model
from client.training.model import create_model


def test_model_and_training_complete():
    ds = prepare_local_dataset()
    model = create_model()
    trained, metrics = train_local_model(model, ds['train'], epochs=1, learning_rate=0.01, batch_size=16)
    assert isinstance(trained, torch.nn.Module)
    assert 'training_loss' in metrics['training_metrics']
    assert metrics['num_samples'] > 0
    assert any(p.requires_grad for p in trained.parameters())


def test_model_parameters_change_after_training():
    ds = prepare_local_dataset()
    model = create_model()
    before = {k: v.clone() for k, v in model.state_dict().items()}
    trained, _ = train_local_model(model, ds['train'], epochs=2, learning_rate=0.01, batch_size=16)
    after = trained.state_dict()
    changed = any(not torch.allclose(before[k], after[k]) for k in before)
    assert changed

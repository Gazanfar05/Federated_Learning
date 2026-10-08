from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from server.federated.anomaly_detection import flag_update

CLIENT_ROOT = Path(__file__).resolve().parents[1] / ".." / "hospital_03_client"
if str(CLIENT_ROOT.resolve()) not in sys.path:
    sys.path.insert(0, str(CLIENT_ROOT.resolve()))

from app.config import load_config
from app.preprocessing import prepare_data
from app.training import build_model, model_update_vector, train_local_model
from app.utils import flatten_state_dict, set_deterministic_seed


def test_extreme_update_is_flagged():
    reference = np.ones(8, dtype=np.float32)
    suspicious = np.full(8, 100.0, dtype=np.float32)
    result = flag_update(suspicious, reference, threshold=0.80)
    assert result["decision"] == "SUSPICIOUS"
    assert float(result["anomaly_score"]) > 0.80


def test_same_seed_reference_update_is_normal():
    set_deterministic_seed(42)
    config = load_config()
    prepared = prepare_data(
        config.data_path,
        batch_size=config.batch_size,
        validation_ratio=config.validation_ratio,
        seed=config.random_seed,
    )

    reference_model = build_model(input_dim=prepared.input_dim)
    local_model = build_model(input_dim=prepared.input_dim)
    result = train_local_model(
        local_model,
        prepared.train_loader,
        prepared.val_loader,
        epochs=config.local_epochs,
        learning_rate=config.learning_rate,
    )

    update_vector = model_update_vector(reference_model, result.model)
    reference_vector = flatten_state_dict(reference_model.state_dict())
    anomaly = flag_update(update_vector, reference_vector, threshold=0.80)

    assert anomaly["decision"] == "NORMAL"
    assert float(anomaly["anomaly_score"]) < 0.80

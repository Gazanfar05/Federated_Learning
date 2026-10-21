from __future__ import annotations

import numpy as np
import pytest
import torch

from server.checkpointing.checkpoint_manager import CheckpointManager
from server.core.coordinator import FederatedCoordinator
from server.federated.robust_aggregation import robust_aggregate
from server.models.diabetes_model import DiabetesMLP


def make_coordinator(tmp_path):
    coordinator = FederatedCoordinator()
    coordinator.checkpoint_manager = CheckpointManager(tmp_path / "checkpoints")
    return coordinator


def test_rejects_wrong_vector_size(tmp_path):
    coordinator = make_coordinator(tmp_path)
    with pytest.raises(ValueError, match="Expected 433 model values"):
        coordinator._vector_to_state_dict(np.zeros(8, dtype=np.float32))


def test_fedavg_uses_submitted_client_models(tmp_path):
    coordinator = make_coordinator(tmp_path)
    initial = coordinator._model_vector().copy()
    version = coordinator.model_version

    coordinator.start_round()
    round_id = coordinator.state.current_round

    first = initial + np.float32(0.01)
    second = initial + np.float32(0.02)

    common = {
        "round_id": round_id,
        "model_version": version,
        "update_hash": "sha256-test-update",
        "timestamp": "2026-10-21T00:00:00Z",
        "reference_model": initial.tolist(),
    }

    result1 = coordinator.submit_update({
        **common,
        "client_id": "hospital_01",
        "num_samples": 10,
        "protected_update": first.tolist(),
    })
    result2 = coordinator.submit_update({
        **common,
        "client_id": "hospital_02",
        "num_samples": 30,
        "protected_update": second.tolist(),
    })

    assert result1["accepted"] is True, result1
    assert result2["accepted"] is True, result2

    completed = coordinator.complete_round("hospital_01", round_id)
    assert completed["status"] == "completed", completed

    expected = (10 * first + 30 * second) / 40
    actual = coordinator._model_vector()

    np.testing.assert_allclose(actual, expected, rtol=1e-5, atol=1e-6)
    assert not np.allclose(actual, initial)
    assert coordinator.model_version == version + 1
    assert completed["metrics"]["available"] is False


def test_rejects_duplicate_client_submission(tmp_path):
    coordinator = make_coordinator(tmp_path)
    initial = coordinator._model_vector()
    coordinator.start_round()
    round_id = coordinator.state.current_round

    payload = {
        "client_id": "hospital_01",
        "round_id": round_id,
        "model_version": coordinator.model_version,
        "num_samples": 10,
        "update_hash": "sha256-duplicate-test",
        "protected_update": (initial + 0.01).tolist(),
        "reference_model": initial.tolist(),
    }

    assert coordinator.submit_update(payload)["accepted"] is True
    duplicate = coordinator.submit_update(payload)
    assert duplicate["accepted"] is False
    assert "already submitted" in duplicate["reason"]


def test_all_flagged_updates_leave_global_model_unchanged():
    global_model = DiabetesMLP()
    client_model = DiabetesMLP()

    with torch.no_grad():
        for parameter in client_model.parameters():
            parameter.fill_(9.0)

    before = {
        key: value.clone()
        for key, value in global_model.state_dict().items()
    }

    result, accepted = robust_aggregate(
        global_model,
        [client_model],
        [10],
        [1.0],
        threshold=0.8,
    )

    assert accepted == []
    for key, value in result.state_dict().items():
        torch.testing.assert_close(value, before[key])


def test_rejects_mismatched_aggregation_inputs():
    model = DiabetesMLP()
    with pytest.raises(ValueError, match="equal lengths"):
        robust_aggregate(model, [model], [10], [], threshold=0.8)

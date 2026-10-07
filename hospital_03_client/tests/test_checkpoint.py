from __future__ import annotations

from app.checkpoint import CheckpointManager, CheckpointState
from app.training import build_model


def test_checkpoint_save_load(tmp_path):
    manager = CheckpointManager(tmp_path)
    model = build_model()
    checkpoint = CheckpointState(
        client_id="hospital_03",
        round_id=1,
        model_version=1,
        model_state_dict=model.state_dict(),
        optimizer_state_dict=None,
        config={"client_id": "hospital_03"},
        metrics={"loss": 0.1},
    )
    saved_path = manager.save(checkpoint)
    loaded = manager.load(saved_path)
    assert loaded.client_id == "hospital_03"
    assert loaded.round_id == 1


def test_resume_latest(tmp_path):
    manager = CheckpointManager(tmp_path)
    model = build_model()
    manager.save(
        CheckpointState(
            client_id="hospital_03",
            round_id=1,
            model_version=1,
            model_state_dict=model.state_dict(),
            optimizer_state_dict=None,
            config={"client_id": "hospital_03"},
            metrics={},
        )
    )
    latest = manager.latest()
    assert latest is not None
    assert latest.round_id == 1

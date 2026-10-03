from __future__ import annotations

from server.checkpointing.checkpoint_manager import CheckpointManager
from server.models.diabetes_model import DiabetesMLP


def test_save_and_restore_checkpoint(tmp_path):
    checkpoint_manager = CheckpointManager(tmp_path)
    model = DiabetesMLP()
    for parameter in model.parameters():
        parameter.data.fill_(2.5)

    checkpoint_manager.save_checkpoint(3, model, {"model_version": 3, "client_participation": ["hospital_01", "hospital_02"]})
    loaded_model, metadata = checkpoint_manager.load_checkpoint(3)

    assert metadata["model_version"] == 3
    assert loaded_model.state_dict()["net.0.weight"].shape == model.state_dict()["net.0.weight"].shape

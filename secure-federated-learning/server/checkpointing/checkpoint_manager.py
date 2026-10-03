from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch

from server.models.diabetes_model import DiabetesMLP


class CheckpointManager:
    def __init__(self, checkpoint_dir: str | Path) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(self, round_id: int, model: DiabetesMLP, metadata: dict[str, Any] | None = None) -> Path:
        round_dir = self.checkpoint_dir / f"round_{round_id:03d}"
        round_dir.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), round_dir / "global_model.pt")
        payload = {
            "round_id": round_id,
            "model_version": metadata.get("model_version", round_id) if metadata else round_id,
            "client_participation": metadata.get("client_participation", []) if metadata else [],
            "metrics": metadata.get("metrics", {}) if metadata else {},
            "privacy_state": metadata.get("privacy_state", {}) if metadata else {},
            "config": metadata.get("config", {}) if metadata else {},
        }
        (round_dir / "metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return round_dir

    def load_checkpoint(self, round_id: int) -> tuple[DiabetesMLP, dict[str, Any]]:
        round_dir = self.checkpoint_dir / f"round_{round_id:03d}"
        if not round_dir.exists():
            raise FileNotFoundError(f"Checkpoint for round {round_id} does not exist.")
        model = DiabetesMLP()
        state_dict = torch.load(round_dir / "global_model.pt", map_location="cpu")
        model.load_state_dict(state_dict)
        metadata = json.loads((round_dir / "metadata.json").read_text(encoding="utf-8"))
        return model, metadata

    def recover_latest_checkpoint(self) -> tuple[DiabetesMLP | None, dict[str, Any] | None]:
        if not self.checkpoint_dir.exists():
            return None, None
        round_dirs = sorted(self.checkpoint_dir.glob("round_*"), key=lambda p: int(p.name.split("_")[-1]))
        if not round_dirs:
            return None, None
        latest_dir = round_dirs[-1]
        model, metadata = self.load_checkpoint(int(latest_dir.name.split("_")[-1]))
        return model, metadata

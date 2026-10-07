from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import torch


@dataclass
class CheckpointState:
    client_id: str
    round_id: int
    model_version: int
    model_state_dict: dict[str, torch.Tensor]
    optimizer_state_dict: dict | None
    config: dict
    metrics: dict


class CheckpointManager:
    def __init__(self, checkpoint_dir: str | Path) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def checkpoint_path(self, round_id: int) -> Path:
        return self.checkpoint_dir / f"round_{round_id:03d}.pt"

    def save(self, state: CheckpointState) -> Path:
        path = self.checkpoint_path(state.round_id)
        torch.save(asdict(state), path)
        return path

    def load(self, path: str | Path) -> CheckpointState:
        data = torch.load(path, map_location="cpu", weights_only=False)
        return CheckpointState(**data)

    def latest(self) -> CheckpointState | None:
        candidates = sorted(self.checkpoint_dir.glob("round_*.pt"))
        if not candidates:
            return None
        return self.load(candidates[-1])

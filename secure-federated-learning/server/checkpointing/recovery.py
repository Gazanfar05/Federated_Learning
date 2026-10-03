from __future__ import annotations

from server.checkpointing.checkpoint_manager import CheckpointManager


def recover_and_continue(checkpoint_manager: CheckpointManager) -> tuple[object | None, dict | None]:
    return checkpoint_manager.recover_latest_checkpoint()

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuntimeState:
    current_round: int = 0
    model_version: int = 1
    running: bool = False
    pending_updates: list[dict] = field(default_factory=list)
    anomaly_log: list[dict] = field(default_factory=list)

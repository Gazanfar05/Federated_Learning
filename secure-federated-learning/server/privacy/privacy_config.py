from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrivacyConfig:
    epsilon_target: float = 2.0
    delta: float = 1e-5
    clipping_norm: float = 1.0
    noise_multiplier: float = 1.0
    rounds: int = 0

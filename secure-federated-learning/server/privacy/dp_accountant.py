from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DPEvent:
    round_id: int
    epsilon: float
    delta: float
    noise_multiplier: float
    clipping_norm: float


class DifferentialPrivacyAccountant:
    """Academic accounting layer for privacy tracking.

    The client side performs the actual clipping and noise addition; the server only
    tracks metadata that is useful for monitoring and a viva demonstration.
    """

    def __init__(self, epsilon_target: float, delta: float, clipping_norm: float, noise_multiplier: float = 1.0) -> None:
        self.epsilon_target = epsilon_target
        self.delta = delta
        self.clipping_norm = clipping_norm
        self.noise_multiplier = noise_multiplier
        self.rounds = 0
        self.events: list[DPEvent] = []

    def register_round(self, round_id: int, client_count: int) -> None:
        self.rounds += 1
        epsilon = self.epsilon_target * (self.rounds / max(1, client_count))
        self.events.append(
            DPEvent(
                round_id=round_id,
                epsilon=epsilon,
                delta=self.delta,
                noise_multiplier=self.noise_multiplier,
                clipping_norm=self.clipping_norm,
            )
        )

    def current_metrics(self) -> dict[str, float | int]:
        latest = self.events[-1] if self.events else DPEvent(0, self.epsilon_target, self.delta, self.noise_multiplier, self.clipping_norm)
        return {
            "epsilon": round(latest.epsilon, 6),
            "delta": round(latest.delta, 12),
            "noise_multiplier": round(latest.noise_multiplier, 6),
            "clipping_norm": round(latest.clipping_norm, 6),
            "rounds": self.rounds,
        }

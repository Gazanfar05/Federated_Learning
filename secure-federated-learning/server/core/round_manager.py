from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrainingRoundState:
    round_id: int
    status: str = "INIT"
    participants: list[str] = field(default_factory=list)
    submitted_clients: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class RoundManager:
    def __init__(self) -> None:
        self.current_round = 0
        self.rounds: dict[int, TrainingRoundState] = {}

    def start_round(self, round_id: int) -> TrainingRoundState:
        self.current_round = round_id
        state = self.rounds.get(round_id)
        if state is None:
            state = TrainingRoundState(round_id=round_id)
            self.rounds[round_id] = state
        state.status = "ACTIVE"
        return state

    def join_round(self, client_id: str, round_id: int) -> TrainingRoundState:
        state = self.rounds.setdefault(round_id, TrainingRoundState(round_id=round_id))
        if client_id not in state.participants:
            state.participants.append(client_id)
        state.status = "ACTIVE"
        self.current_round = round_id
        return state

    def mark_submission(self, client_id: str, round_id: int) -> TrainingRoundState:
        state = self.rounds.setdefault(round_id, TrainingRoundState(round_id=round_id))
        if client_id not in state.submitted_clients:
            state.submitted_clients.append(client_id)
        return state

    def complete_round(self, round_id: int) -> TrainingRoundState:
        state = self.rounds.setdefault(round_id, TrainingRoundState(round_id=round_id))
        state.status = "COMPLETED"
        return state

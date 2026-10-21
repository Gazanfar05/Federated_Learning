from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RoundSubmission:
    client_id: str
    round_id: int
    model_version: int
    num_samples: int
    update_hash: str
    protected_update: list[float]
    timestamp: str


@dataclass
class RoundRecord:
    round_id: int
    participants: list[str] = field(default_factory=list)
    submissions: list[RoundSubmission] = field(default_factory=list)
    status: str = "INIT"
    metrics: dict[str, Any] = field(default_factory=dict)


class RoundStore:
    def __init__(self) -> None:
        self._rounds: dict[int, RoundRecord] = {}

    def ensure_round(self, round_id: int) -> RoundRecord:
        record = self._rounds.get(round_id)
        if record is None:
            record = RoundRecord(round_id=round_id)
            self._rounds[round_id] = record
        return record

    def add_submission(self, round_id: int, submission: RoundSubmission) -> None:
        record = self.ensure_round(round_id)
        record.submissions.append(submission)
        if submission.client_id not in record.participants:
            record.participants.append(submission.client_id)

    def get(self, round_id: int) -> RoundRecord | None:
        return self._rounds.get(round_id)

    def list(self) -> list[RoundRecord]:
        return [self._rounds[key] for key in sorted(self._rounds)]
